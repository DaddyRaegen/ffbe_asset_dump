package O1;

import java.io.*;
import java.net.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.Inflater;
import java.util.zip.InflaterInputStream;

/** APK-pinned data files. Network access is restricted to the download worker. */
public final class ExtraContent {
    public static final class Entry {
        public final String path, hash, url;
        public final long size, offset, wireSize, sourceSize;
        public final int method;
        public volatile long transferred;
        Entry(String[] p) throws IOException {
            path=p[0]; hash=p[1]; size=Long.parseLong(p[2]); url=p[3];
            offset=Long.parseLong(p[4]); wireSize=Long.parseLong(p[5]); method=Integer.parseInt(p[6]); sourceSize=Long.parseLong(p[7]);
            if (!path.matches("(?:(side_stories|story_ports|battle|encyclopedia)/[A-Za-z0-9_.-]+|side_stories/r2_scene_(jp|gl)/[a-f0-9]{16}/[A-Za-z0-9_.-]+[.]cpk)")
                || path.contains("..") || !hash.matches("[a-f0-9]{64}") || size<1 || offset<0 || wireSize<1
                || offset>sourceSize-wireSize || (method!=0 && method!=8)
                || !(url.startsWith("https://ffbe.luminest.io/downloads/beta/") || url.startsWith("https://ffbe.luminest.io/downloads/content/") || ResumableTransfer.githubRelease(url))) throw new IOException("Invalid content entry");
            ResumableTransfer.validateSource(url,sourceSize);
        }
    }
    private static Map<String,Entry> entries;
    private static Map<String,List<Entry>> byHash;
    private static final Map<String,File> verified = new HashMap<>();

    static File files() throws Exception {
        Object app=Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null);
        if(app==null)throw new IOException("Application unavailable");
        return (File)Class.forName("android.content.Context").getMethod("getFilesDir").invoke(app);
    }
    private static InputStream bundled(String name) throws Exception {
        Object app=Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null);
        Object assets=Class.forName("android.content.Context").getMethod("getAssets").invoke(app);
        return (InputStream)Class.forName("android.content.res.AssetManager").getMethod("open",String.class).invoke(assets,name);
    }
    static synchronized void load() throws Exception {
        if(entries!=null)return;
        Map<String,Entry> next=new LinkedHashMap<>(); Map<String,List<Entry>> hashes=new LinkedHashMap<>();
        try(BufferedReader r=new BufferedReader(new InputStreamReader(bundled("content_delivery.tsv"),"UTF-8"))){
            if(!"ffbe-content-v1".equals(r.readLine()))throw new IOException("Invalid content manifest");
            String line;
            while((line=r.readLine())!=null){
                String[] p=line.split("\t",-1); if(p.length!=8)throw new IOException("Invalid content row");
                Entry e=new Entry(p); if(next.put(e.path,e)!=null)throw new IOException("Duplicate content path");
                List<Entry> aliases=hashes.get(e.hash);if(aliases==null){aliases=new ArrayList<>();hashes.put(e.hash,aliases);}
                if(!aliases.isEmpty() && aliases.get(0).size!=e.size)throw new IOException("Inconsistent content hash");
                aliases.add(e);
            }
        }
        if(next.isEmpty())throw new IOException("Empty content manifest");
        entries=next;byHash=hashes;
    }
    static File target(Entry e) throws Exception {
        String[] p=e.path.split("/",2);
        String dir=p[0].equals("story_ports")?"story_ports/pilot1":p[0].equals("battle")?"battle/r8":p[0].equals("encyclopedia")?"encyclopedia/r7":p[0];
        return new File(files(),dir+"/"+e.hash+"/"+p[1]);
    }
    private static File partial(Entry e) throws Exception {return new File(files(),"content_delivery/"+e.hash+".part");}
    private static boolean valid(File f,Entry e) throws Exception {return f.isFile()&&f.length()==e.size&&e.hash.equals(hash(f));}
    private static synchronized File cached(Entry e) throws Exception {
        File f=verified.get(e.hash);
        if(f!=null&&f.isFile()&&f.length()==e.size)return f;
        verified.remove(e.hash);
        for(Entry alias:byHash.get(e.hash)) {f=target(alias);if(valid(f,e)){verified.put(e.hash,f);return f;}}
        return null;
    }
    public static List<Entry> missing() throws Exception {
        load();List<Entry> pending=new ArrayList<>();
        for(List<Entry> aliases:byHash.values()) {Entry e=aliases.get(0);if(cached(e)==null){e.transferred=Math.min(partial(e).length(),e.wireSize);pending.add(e);}}
        return pending;
    }
    public static InputStream open(String name) throws Exception {
        try{return bundled(name);}catch(Exception absent){}
        load();Entry e=entries.get(name);
        if(e==null)return bundled(name);
        File f=cached(e); if(f==null)throw new FileNotFoundException("Download required: "+name);
        return new FileInputStream(f);
    }
    public static void download(final Entry e) throws Exception {
        if(cached(e)!=null){e.transferred=e.wireSize;return;}
        File part=partial(e);
        ResumableTransfer.fetch(e.url,part,e.offset,e.wireSize,e.sourceSize,new ResumableTransfer.Progress(){public void received(long n){e.transferred=n;}});
        finish(e,part);
    }
    private static final class CorruptContent extends IOException {CorruptContent(String message){super(message);}}
    private static void finish(Entry e,File part) throws Exception {
        File dest=target(e), temp=new File(part.getPath()+".unpack");
        Inflater inflater=e.method==8?new Inflater(true):null;
        try {
            MessageDigest digest=MessageDigest.getInstance("SHA-256");long length=0;
            try(InputStream raw=new FileInputStream(part);
                InputStream in=inflater==null?raw:new InflaterInputStream(raw,inflater,65536);
                FileOutputStream out=new FileOutputStream(temp)){
                byte[] b=new byte[65536];int n;
                while((n=in.read(b))!=-1){length+=n;if(length>e.size)throw new CorruptContent("Oversized content");digest.update(b,0,n);out.write(b,0,n);}
                out.getFD().sync();
            }
            if(length!=e.size || !e.hash.equals(hex(digest.digest())))throw new CorruptContent("Content verification failed");
            File dir=dest.getParentFile();if(!dir.isDirectory()&&!dir.mkdirs()&&!dir.isDirectory())throw new IOException("Cannot create content directory");
            if(dest.exists()&&!dest.delete())throw new IOException("Cannot replace damaged content");
            if(!temp.renameTo(dest))throw new IOException("Cannot finish content download");
            synchronized(ExtraContent.class){verified.put(e.hash,dest);}
            part.delete();e.transferred=e.wireSize;
        } catch(Exception error){temp.delete();if(error instanceof CorruptContent||error instanceof java.util.zip.ZipException){part.delete();e.transferred=0;}throw error;}
        finally{if(inflater!=null)inflater.end();}
    }
    /** Adjacent missing ZIP members share a request; cached gaps are never re-fetched. */
    public static List<List<Entry>> batches(List<Entry> missing) throws Exception {
        List<Entry> sorted=new ArrayList<>(missing);
        Collections.sort(sorted,new Comparator<Entry>(){public int compare(Entry a,Entry b){int c=a.url.compareTo(b.url);return c!=0?c:Long.compare(a.offset,b.offset);}});
        List<List<Entry>> batches=new ArrayList<>();List<Entry> batch=null;Entry previous=null;
        for(Entry e:sorted){
            boolean resume=partial(e).length()>0;
            if(batch==null||resume||ResumableTransfer.githubRelease(e.url)||!previous.url.equals(e.url)||previous.sourceSize!=e.sourceSize
                || e.offset<previous.offset+previous.wireSize||e.offset-previous.offset-previous.wireSize>4096
                || e.offset+e.wireSize-batch.get(0).offset>16*1024*1024L){batch=new ArrayList<>();batches.add(batch);}
            batch.add(e);previous=e;if(resume)batch=null;
        }
        return batches;
    }
    public static void downloadBatch(List<Entry> batch) throws Exception {
        if(batch.size()==1){download(batch.get(0));return;}
        Entry first=batch.get(0),last=batch.get(batch.size()-1);
        long start=first.offset,end=last.offset+last.wireSize-1,position=start;
        HttpURLConnection c=(HttpURLConnection)new URL(first.url).openConnection();
        try {
            c.setConnectTimeout(15000);c.setReadTimeout(60000);c.setInstanceFollowRedirects(false);
            c.setRequestProperty("Accept-Encoding","identity");c.setRequestProperty("Range","bytes="+start+"-"+end);
            if(c.getResponseCode()!=206||!("bytes "+start+"-"+end+"/"+first.sourceSize).equals(c.getHeaderField("Content-Range")))throw new IOException("Server did not honor the content range");
            try(InputStream in=c.getInputStream()){
                byte[] b=new byte[65536];
                for(Entry e:batch){
                    while(position<e.offset){int n=in.read(b,0,(int)Math.min(b.length,e.offset-position));if(n<0)throw new EOFException();position+=n;}
                    File part=partial(e),dir=part.getParentFile();if(!dir.isDirectory()&&!dir.mkdirs()&&!dir.isDirectory())throw new IOException("Cannot create download directory");
                    e.transferred=0;
                    try(FileOutputStream out=new FileOutputStream(part)){
                        long left=e.wireSize;
                        while(left>0){int n=in.read(b,0,(int)Math.min(b.length,left));if(n<0)throw new EOFException();out.write(b,0,n);left-=n;position+=n;e.transferred+=n;}
                        out.getFD().sync();
                    }
                    finish(e,part);
                }
                if(position!=end+1||in.read()!=-1)throw new IOException("Unexpected content range length");
            }
        }finally{c.disconnect();}
    }
    private static String hex(byte[] bytes){StringBuilder s=new StringBuilder(64);for(byte b:bytes){int n=b&255;if(n<16)s.append('0');s.append(Integer.toHexString(n));}return s.toString();}
    static String hash(File f)throws Exception {MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}return hex(d.digest());}
}
