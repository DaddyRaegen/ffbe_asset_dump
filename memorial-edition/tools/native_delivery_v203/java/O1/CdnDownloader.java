package O1;

import android.content.Context;
import android.util.Log;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

/** Base-game cache compatible with previous releases; no manifest network dependency. */
public final class CdnDownloader {
    private static final String TAG="FFBE-EN";
    private static final String[] PACK_NAMES={"on_demand_asset","on_demand_asset2","on_demand_asset3","on_demand_asset4","on_demand_asset5","on_demand_asset6"};
    private static String localAssetDir;
    private static volatile boolean checking,downloading,failed;
    private static volatile List<FileEntry> pending=Collections.emptyList();
    private static volatile int totalCount;
    private static volatile long totalSize;
    static final class FileEntry {
        final String pack,name,hash,url;final long size;
        volatile long received;volatile boolean complete;
        FileEntry(String[] p)throws IOException{
            pack=p[0];name=p[1];size=Long.parseLong(p[2]);hash=p[3];url=p[4];
            if(!Arrays.asList(PACK_NAMES).contains(pack)||!name.matches("[A-Za-z0-9_.-]+")||name.contains("..")||size<1||!hash.matches("[a-f0-9]{64}")||!(url.equals("https://ffbe.luminest.io/downloads/base/v1/"+hash+".bin")||ResumableTransfer.githubRelease(url)||LanTestTransport.allowed(url)))throw new IOException("Invalid base-game file");
            ResumableTransfer.validateSource(url,size);
        }
        File destination(){return new File(localAssetDir,pack+"/199/199/assets/"+name);}
        File partial(){return new File(destination().getPath()+".tmp");}
    }
    private static Context context()throws Exception{return (Context)Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null);}
    public static synchronized void initLocalDir(){
        if(localAssetDir!=null)return;
        try {
            Context c=context();File dir=c.getExternalFilesDir(null);if(dir==null)dir=c.getFilesDir();
            localAssetDir=new File(dir,"assetpacks").getAbsolutePath();
        }catch(Exception e){localAssetDir="/data/data/com.square_enix.ffbejpn/files/assetpacks";}
    }
    public static String findLocalFile(String name){
        if(localAssetDir==null)initLocalDir();
        for(String pack:PACK_NAMES){File f=new File(localAssetDir,pack+"/199/199/assets/"+name);if(f.isFile()&&f.length()>0)return f.getAbsolutePath();}
        return "";
    }
    public static void checkAssets(){
        checking=true;failed=false;initLocalDir();
        try {
            List<FileEntry> next=new ArrayList<>();Set<String> names=new HashSet<>();long size=0;int listed=0;
            try(BufferedReader r=new BufferedReader(new InputStreamReader(context().getAssets().open("base_delivery.tsv"),"UTF-8"))){
                if(!"ffbe-base-v1".equals(r.readLine()))throw new IOException("Invalid base-game catalog");
                String line;while((line=r.readLine())!=null){String[] p=line.split("\t",-1);if(p.length!=5)throw new IOException("Invalid base-game catalog row");
                    FileEntry e=new FileEntry(p);listed++;if(!names.add(e.pack+"/"+e.name))throw new IOException("Duplicate base-game file");
                    File f=e.destination();if(f.isFile()&&f.length()==e.size&&e.hash.equals(ExtraContent.hash(f)))continue;
                    e.received=e.partial().length()<=e.size?e.partial().length():0;next.add(e);size+=e.size;
                }
            }
            if(listed==0)throw new IOException("Empty base-game catalog");
            Collections.sort(next,new Comparator<FileEntry>(){public int compare(FileEntry a,FileEntry b){return Long.compare(b.size,a.size);}});
            pending=next;totalCount=next.size();totalSize=size;
            Log.i(TAG,"Base files missing: "+totalCount+"; saved partial bytes: "+getDownloadedSize());
        }catch(Exception e){failed=true;Log.e(TAG,"Base content check failed",e);throw new IllegalStateException("Cannot check base game files",e);}
        finally{checking=false;}
    }
    public static synchronized void startDownload(){
        startDownload(new ResumableTransfer.Attempt());
    }
    static synchronized void startDownload(final ResumableTransfer.Attempt attempt){
        if(downloading)return;downloading=true;
        new Thread(new Runnable(){public void run(){
            ExecutorService pool=Executors.newFixedThreadPool(4);
            try{
                final Queue<FileEntry> queue=new ArrayDeque<>();
                for(FileEntry e:pending)if(!e.complete)queue.add(e);
                for(int worker=0;worker<4;worker++)pool.submit(new Runnable(){public void run(){
                    FileEntry e;while((e=attempt.next(queue))!=null){
                        try{download(e);e.complete=true;}
                        catch(Exception error){attempt.pause();Log.e(TAG,"Base download paused: "+e.name,error);return;}
                    }
                }});
                pool.shutdown();while(!pool.awaitTermination(1,TimeUnit.SECONDS)){}
            }catch(InterruptedException e){Thread.currentThread().interrupt();pool.shutdownNow();}
            finally{downloading=false;}
        }},"FFBE-Base-Downloads").start();
    }
    static void download(final FileEntry e)throws Exception {
        File destination=e.destination(),part=e.partial();
        if(destination.isFile()&&destination.length()==e.size&&e.hash.equals(ExtraContent.hash(destination))){e.received=e.size;return;}
        if(part.length()>0)Log.i(TAG,"Resuming "+e.name+" at byte "+part.length());
        for(int repair=0;repair<2;repair++){
            ResumableTransfer.fetch(e.url,part,0,e.size,e.size,new ResumableTransfer.Progress(){public void received(long n){e.received=n;}});
            if(!e.hash.equals(ExtraContent.hash(part))){
                if(!part.delete())throw new IOException("Cannot replace damaged download");e.received=0;
                if(repair==0)continue;throw new IOException("Base-game file verification failed");
            }
            if(destination.exists()&&!destination.delete())throw new IOException("Cannot replace damaged game file");
            if(!part.renameTo(destination))throw new IOException("Cannot save downloaded game file");
            e.received=e.size;Log.i(TAG,"Verified base download: "+e.name);return;
        }
    }
    public static int getDownloadedCount(){int n=0;for(FileEntry e:pending)if(e.complete)n++;return n;}
    public static long getDownloadedSize(){long n=0;for(FileEntry e:pending)n+=e.received;return n;}
    public static int getTotalCount(){return totalCount;}
    public static long getTotalSize(){return totalSize;}
    public static boolean getIsDownloading(){return downloading;}
    public static boolean getIsCheckingState(){return checking;}
    public static boolean getNeedsDownload(){return failed||getDownloadedCount()<totalCount;}
    public static void setDownloadedCount(int n){}
    public static void setDownloadedSize(long n){}
    public static void setIsDownloading(boolean value){if(!value)downloading=false;}
}
