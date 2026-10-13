package O1;

import java.io.*;
import java.net.*;
import java.text.SimpleDateFormat;
import java.util.*;

/** Exact byte ranges; unfinished bytes survive network failure and process death. */
public final class ResumableTransfer {
    /** One shared attempt for base and extra files. Already admitted transfers finish normally. */
    static final class Attempt {
        private boolean paused;
        synchronized <T> T next(Queue<T> queue){return paused?null:queue.poll();}
        synchronized void pause(){paused=true;}
    }
    public interface Progress { void received(long bytes); }
    interface Delay { void sleep(long millis) throws InterruptedException; }
    static Delay delay=new Delay(){public void sleep(long ms)throws InterruptedException{Thread.sleep(ms);}};
    static final int ATTEMPTS=5;
    interface Clock {long millis();}
    static Clock clock=new Clock(){public long millis(){return System.nanoTime()/1000000L;}};
    private static final class Redirect {
        final URL url;final long savedAt;
        Redirect(URL url){this.url=url;savedAt=clock.millis();}
    }
    private static final Map<String,Redirect> redirects=new HashMap<>();
    static synchronized void clearRedirectCache(){redirects.clear();}
    private static synchronized Redirect cachedRedirect(Source source){
        if(!source.packed)return null;
        String key=source.url.toExternalForm();Redirect entry=redirects.get(key);
        if(entry!=null&&(clock.millis()-entry.savedAt<0||clock.millis()-entry.savedAt>=120000)){redirects.remove(key);return null;}
        return entry;
    }
    private static synchronized void forgetRedirect(Source source,Redirect entry){
        String key=source.url.toExternalForm();if(redirects.get(key)==entry)redirects.remove(key);
    }
    private static synchronized void rememberRedirect(Source source,URL finalUrl){
        if(source.packed&&releaseAsset(finalUrl)){
            String key=source.url.toExternalForm();Redirect previous=redirects.get(key);
            if(previous==null||!previous.url.toExternalForm().equals(finalUrl.toExternalForm()))redirects.put(key,new Redirect(finalUrl));
        }
    }
    private static final class UnsafeSource extends IOException {UnsafeSource(String message){super(message);}}
    private static final class Source {
        final URL url;final long start,total;final boolean packed,github;
        Source(URL url,long start,long total,boolean packed,boolean github){this.url=url;this.start=start;this.total=total;this.packed=packed;this.github=github;}
    }
    private static boolean https(URL url){return "https".equalsIgnoreCase(url.getProtocol())&&url.getUserInfo()==null&&(url.getPort()==-1||url.getPort()==443);}
    static boolean githubRelease(String value){
        try{URL u=new URL(value);return https(u)&&"github.com".equalsIgnoreCase(u.getHost())&&u.getPath().matches("/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/releases/download/[^/]+/[^/]+");}
        catch(Exception e){return false;}
    }
    static void validateSource(String value,long sourceSize)throws IOException {source(value,sourceSize);}
    private static Source source(String value,long sourceSize)throws IOException {
        URL u=new URL(value);if((!https(u)&&!LanTestTransport.allowed(u))||sourceSize<1)throw new UnsafeSource("Invalid HTTPS or pinned LAN test source");
        boolean github=githubRelease(value);String fragment=u.getRef();
        if(fragment==null)return new Source(u,0,sourceSize,false,github);
        if(!github||!fragment.matches("ffbe-range=[0-9]+:[0-9]+:[0-9]+"))throw new UnsafeSource("Invalid packed download source");
        String[] fields=fragment.substring("ffbe-range=".length()).split(":");
        try{
            long start=Long.parseLong(fields[0]),size=Long.parseLong(fields[1]),total=Long.parseLong(fields[2]);
            if(size!=sourceSize||size<1||total<size||start>total-size)throw new UnsafeSource("Invalid packed download bounds");
            return new Source(new URL(value.substring(0,value.indexOf('#'))),start,total,true,true);
        }catch(NumberFormatException e){throw new UnsafeSource("Packed download bounds overflow");}
    }
    private static boolean releaseAsset(URL u){return https(u)&&u.getRef()==null&&("release-assets.githubusercontent.com".equalsIgnoreCase(u.getHost())||"objects.githubusercontent.com".equalsIgnoreCase(u.getHost()));}
    private static final class HttpFailure extends IOException {
        final int status; final long retryAfter;
        HttpFailure(int status,long retryAfter){super("Download server returned HTTP "+status);this.status=status;this.retryAfter=retryAfter;}
    }
    public static void fetch(String url,File partial,long offset,long size,long sourceSize,Progress progress)throws Exception {
        if(size<1||offset<0||offset>sourceSize-size)throw new IOException("Invalid download range");
        Source source=source(url,sourceSize);
        File parent=partial.getParentFile();
        if(!parent.isDirectory()&&!parent.mkdirs()&&!parent.isDirectory())throw new IOException("Cannot create download folder");
        if(partial.length()>size)try(RandomAccessFile f=new RandomAccessFile(partial,"rw")){f.setLength(0);}
        progress.received(partial.length());
        for(int attempt=0;;attempt++){
            try { once(source,partial,offset,size,sourceSize,progress); return; }
            catch(IOException error){
                progress.received(partial.length());
                if(error instanceof UnsafeSource)throw error;
                if(attempt+1>=ATTEMPTS)throw error;
                long wait=1000L<<attempt;
                if(error instanceof HttpFailure){
                    HttpFailure h=(HttpFailure)error;
                    if(h.status!=408&&h.status!=429&&h.status<500)throw error;
                    if(h.retryAfter>900000)throw error;
                    wait=Math.max(wait,h.retryAfter);
                }
                delay.sleep(wait);
            }
        }
    }
    private static void once(Source source,File partial,long offset,long size,long sourceSize,Progress progress)throws IOException {
        long have=partial.length();if(have==size)return;
        long start=source.start+offset+have,end=source.start+offset+size-1;
        HttpURLConnection c=open(source,start,end);
        try {
            int status=c.getResponseCode();
            if(status!=206&&status!=200)throw new HttpFailure(status,retryAfter(c.getHeaderField("Retry-After")));
            boolean entire=!source.packed&&status==200&&have==0&&offset==0&&size==sourceSize;
            if(!entire && (status!=206||!("bytes "+start+"-"+end+"/"+source.total).equals(c.getHeaderField("Content-Range"))))
                throw new IOException("Download server returned a different byte range");
            String length=c.getHeaderField("Content-Length");
            if(length!=null && !length.equals(Long.toString(size-have)))throw new IOException("Download length changed");
            String encoding=c.getHeaderField("Content-Encoding");
            if(encoding!=null&&!encoding.equalsIgnoreCase("identity"))throw new IOException("Unexpected download encoding");
            rememberRedirect(source,c.getURL());
            try(InputStream in=c.getInputStream();FileOutputStream out=new FileOutputStream(partial,true)){
                byte[] b=new byte[65536];long left=size-have;
                while(left>0){int n=in.read(b,0,(int)Math.min(b.length,left));if(n<0)throw new EOFException("Connection interrupted");if(n==0)continue;
                    out.write(b,0,n);left-=n;have+=n;progress.received(have);
                }
                if(in.read()!=-1)throw new IOException("Unexpected extra download bytes");
                out.getFD().sync();
            }
        }finally{c.disconnect();}
    }
    private static HttpURLConnection open(Source source,long start,long end)throws IOException {
        Redirect cached=cachedRedirect(source);
        if(cached!=null){
            HttpURLConnection c=follow(source,cached.url,start,end);int status=c.getResponseCode();
            if(status!=401&&status!=403)return c;
            c.disconnect();forgetRedirect(source,cached);
        }
        // A rejected signed URL is refreshed through the original public release URL once.
        return follow(source,source.url,start,end);
    }
    private static HttpURLConnection follow(Source source,URL url,long start,long end)throws IOException {
        for(int hops=0;;hops++){
            HttpURLConnection c=(HttpURLConnection)url.openConnection();boolean keep=false;
            try{
                c.setConnectTimeout(15000);c.setReadTimeout(20000);c.setInstanceFollowRedirects(false);c.setAllowUserInteraction(false);c.setUseCaches(false);
                c.setRequestProperty("Accept-Encoding","identity");c.setRequestProperty("Range","bytes="+start+"-"+end);
                // Each hop is a fresh public request: no credentials or previous-hop headers are copied.
                int status=c.getResponseCode();
                if(status!=301&&status!=302&&status!=303&&status!=307&&status!=308){keep=true;return c;}
                if(!source.github)throw new HttpFailure(status,0);
                if(hops>=4)throw new UnsafeSource("Too many release download redirects");
                String location=c.getHeaderField("Location");if(location==null||location.trim().isEmpty())throw new UnsafeSource("Missing release download redirect");
                URL next=new URL(url,location);if(!releaseAsset(next))throw new UnsafeSource("Unsafe release download redirect");
                url=next;
            }finally{if(!keep)c.disconnect();}
        }
    }
    private static long retryAfter(String value){
        if(value==null)return 0;
        try{long seconds=Long.parseLong(value.trim());return seconds<=0?0:seconds>900?900001:seconds*1000;}catch(Exception ignored){}
        try{SimpleDateFormat f=new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss zzz",Locale.US);f.setTimeZone(TimeZone.getTimeZone("GMT"));return Math.max(0,f.parse(value).getTime()-System.currentTimeMillis());}catch(Exception ignored){return 0;}
    }
}
