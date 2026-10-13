package O1;

import java.io.*;
import java.net.*;
import java.security.MessageDigest;
import android.util.AtomicFile;
import java.util.*;
import java.util.zip.Inflater;
import java.util.zip.InflaterInputStream;

/** APK baseline plus optional verified data snapshots. Network runs only in startup workers. */
public final class ExtraContent {
    public interface ProgressListener {void changed(List<Entry> pending,long total);}
    public static final class Entry {
        public final String path, hash, url;
        public final long size, offset, wireSize, sourceSize;
        public final int method;
        public volatile long transferred;
        Entry(String[] p) throws IOException {
            path=p[0]; hash=p[1]; size=Long.parseLong(p[2]); url=p[3];
            offset=Long.parseLong(p[4]); wireSize=Long.parseLong(p[5]); method=Integer.parseInt(p[6]); sourceSize=Long.parseLong(p[7]);
            if (!GameAssets.safePath(path)
                || path.contains("..") || !hash.matches("[a-f0-9]{64}") || size<1 || offset<0 || wireSize<1
                || offset>sourceSize-wireSize || (method!=0 && method!=8)
                || !(url.startsWith("https://ffbe.luminest.io/downloads/beta/") || url.startsWith("https://ffbe.luminest.io/downloads/content/") || ResumableTransfer.githubRelease(url) || LanTestTransport.allowed(url))) throw new IOException("Invalid content entry");
            ResumableTransfer.validateSource(url,sourceSize);
        }
    }
    private static Map<String,Entry> entries;
    private static Map<String,Entry> baseline, candidate;
    private static Map<String,List<Entry>> byHash;
    private static final Map<String,File> verified = new HashMap<>();

    static File files() throws Exception {
        Object app=Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null);
        if(app==null)throw new IOException("Application unavailable");
        return (File)Class.forName("android.content.Context").getMethod("getFilesDir").invoke(app);
    }
    static InputStream bundled(String name) throws Exception {
        Object app=Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null);
        Object assets=Class.forName("android.content.Context").getMethod("getAssets").invoke(app);
        try{return (InputStream)Class.forName("android.content.res.AssetManager").getMethod("open",String.class).invoke(assets,name);}
        catch(java.lang.reflect.InvocationTargetException wrapped){Throwable cause=wrapped.getCause();if(cause instanceof Exception)throw (Exception)cause;if(cause instanceof Error)throw (Error)cause;throw new IOException("Cannot read bundled asset",wrapped);}
    }
    static synchronized void load() throws Exception {
        if(entries!=null)return;
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        try(InputStream in=bundled("content_delivery.tsv")){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){if(out.size()>8*1024*1024-n)throw new IOException("Oversized content manifest");out.write(b,0,n);}}
        byte[] bytes=out.toByteArray();baseline=parseCatalog(bytes);
        entries=GameAssets.initialize(bytes,baseline);byHash=hashes(entries);
    }
    static Map<String,Entry> parseCatalog(byte[] bytes) throws Exception {
        if(bytes.length>8*1024*1024)throw new IOException("Oversized content manifest");
        Map<String,Entry> next=new LinkedHashMap<>();
        try(BufferedReader r=new BufferedReader(new InputStreamReader(new ByteArrayInputStream(bytes),"UTF-8"))){
            if(!"ffbe-content-v1".equals(r.readLine()))throw new IOException("Invalid content manifest");
            String line;
            while((line=r.readLine())!=null){
                String[] p=line.split("\t",-1); if(p.length!=8)throw new IOException("Invalid content row");
                Entry e=new Entry(p); if(next.put(e.path,e)!=null)throw new IOException("Duplicate content path");
                if(next.size()>50000)throw new IOException("Too many content rows");
            }
        }
        if(next.isEmpty())throw new IOException("Empty content manifest");
        hashes(next);return next;
    }
    private static Map<String,List<Entry>> hashes(Map<String,Entry> catalog) throws IOException {
        Map<String,List<Entry>> hashes=new LinkedHashMap<>();
        for(Entry e:catalog.values()){
            List<Entry> aliases=hashes.get(e.hash);if(aliases==null){aliases=new ArrayList<>();hashes.put(e.hash,aliases);}
            if(!aliases.isEmpty()&&aliases.get(0).size!=e.size)throw new IOException("Inconsistent content hash");aliases.add(e);
        }
        return hashes;
    }
    /** Called once by the existing startup check worker, before downloads and table preparation. */
    public static synchronized void checkHostedUpdate() throws Exception {
        load();candidate=GameAssets.checkUpdate(entries);
    }
    public static synchronized boolean activateHostedUpdate() throws Exception {
        if(candidate==null)return false;
        // Native CPKs and table handles stay on one graph for the entire process.
        if(!GameAssets.stageNextLaunch(candidate))return false;
        candidate=null;return false;
    }
    static File target(Entry e) throws Exception {
        String[] p=e.path.split("/",2);
        String dir=p[0].equals("story_ports")?"story_ports/pilot1":p[0].equals("battle")?"battle/r8":p[0].equals("encyclopedia")?"encyclopedia/r7":p[0];
        if(!p[0].matches("side_stories|story_ports|battle|encyclopedia"))return new File(files(),"game_assets/objects/"+e.hash+"/"+e.path);
        return new File(files(),dir+"/"+e.hash+"/"+p[1]);
    }
    private static File partial(Entry e) throws Exception {return new File(files(),"content_delivery/"+e.hash+".part");}
    private static boolean valid(File f,Entry e) throws Exception {return f.isFile()&&f.length()==e.size&&e.hash.equals(hash(f));}
    private static File hashIndex(Entry e)throws Exception{return new File(files(),"game_assets/hash_index/"+e.hash);}
    private static File remember(Entry e,File source)throws Exception{
        File index=hashIndex(e);if(index.isFile()&&valid(index,e)){verified.put(e.hash,index);return index;}
        // File.exists follows links; delete also removes a dangling owned index.
        if(!index.delete()&&index.exists())throw new IOException("Cannot replace damaged hash index");
        File parent=index.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs()&&!parent.isDirectory())throw new IOException("Content hash index unavailable");
        GameAssets.linker.create(index,source);verified.put(e.hash,index);return index;
    }
    /** Copy only inventory-admitted APK bytes; preserves remote partials and user data. */
    static synchronized File seedBundled(Entry e)throws Exception {
        File dest=target(e);boolean write=!valid(dest,e);AtomicFile atomic=null;FileOutputStream out=null;
        try {
            if(write){File parent=dest.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs()&&!parent.isDirectory())throw new IOException("Startup cache unavailable");atomic=new AtomicFile(dest);out=atomic.startWrite();}
            MessageDigest digest=MessageDigest.getInstance("SHA-256");long length=0;
            try(InputStream in=bundled(e.path)){byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1){length+=n;if(length>e.size)throw new IOException("Bundled startup size disagrees: "+e.path);digest.update(buffer,0,n);if(out!=null)out.write(buffer,0,n);}}
            if(length!=e.size||!e.hash.equals(hex(digest.digest())))throw new IOException("Bundled startup checksum disagrees: "+e.path);
            if(out!=null){out.getFD().sync();atomic.finishWrite(out);out=null;}
            verified.remove(e.hash);return remember(e,dest);
        } finally {if(out!=null)atomic.failWrite(out);}
    }
    private static synchronized File cached(Entry e) throws Exception {
        return available(e,candidate!=null&&candidate.containsValue(e)?candidate:entries);
    }
    /** Optional update failure must not prevent an already complete installation from opening offline. */
    public static synchronized boolean retainCurrentContent() throws Exception {
        if(candidate==null||!ready(entries))return false;
        candidate=null;GameAssets.discardPending();return true;
    }
    static synchronized File available(Entry e,Map<String,Entry> catalog) throws Exception {
        File f=verified.get(e.hash);
        if(f!=null&&f.isFile()&&f.length()==e.size&&(!BundledAssets.contains(e)||valid(f,e)))return f;
        verified.remove(e.hash);
        f=hashIndex(e);if(valid(f,e)){verified.put(e.hash,f);return f;}
        for(Entry alias:catalog.values())if(alias.hash.equals(e.hash)&&alias.size==e.size){f=target(alias);if(valid(f,e))return remember(e,f);}
        return BundledAssets.contains(e)?seedBundled(e):null;
    }
    static synchronized boolean ready(Map<String,Entry> catalog) throws Exception {
        for(List<Entry> aliases:hashes(catalog).values())if(available(aliases.get(0),catalog)==null)return false;return true;
    }
    public static synchronized List<Entry> missingBoot() throws Exception {
        load();List<Entry> result=new ArrayList<>();for(List<Entry> aliases:byHash.values()){Entry selected=null;for(Entry e:aliases)if(GameAssets.bootPath(e.path)){selected=e;break;}if(selected!=null&&available(selected,entries)==null){selected.transferred=Math.min(partial(selected).length(),selected.wireSize);result.add(selected);}}return result;
    }
    public static synchronized Map<String,Entry> current(){return entries;}
    public static synchronized List<Entry> missing() throws Exception {
        load();List<Entry> pending=new ArrayList<>();
        // Current handles remain active this process. Download their missing objects
        // as well as future changes; a staged revision cannot strand current tables.
        Map<String,List<Entry>> needed=new LinkedHashMap<>(byHash);
        if(candidate!=null)for(List<Entry> aliases:hashes(candidate).values())if(!needed.containsKey(aliases.get(0).hash))needed.put(aliases.get(0).hash,aliases);
        for(List<Entry> aliases:needed.values()) {Entry e=aliases.get(0);Map<String,Entry> catalog=candidate!=null&&candidate.containsValue(e)?candidate:entries;if(available(e,catalog)==null){e.transferred=Math.min(partial(e).length(),e.wireSize);pending.add(e);}}
        return pending;
    }
    public static synchronized InputStream open(String name) throws Exception {
        load();Entry e=entries.get(name);
        if(e==null)return bundled(name);
        File f=available(e,entries);if(f==null)throw new FileNotFoundException("Download required: "+name);
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
            synchronized(ExtraContent.class){remember(e,dest);}
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
