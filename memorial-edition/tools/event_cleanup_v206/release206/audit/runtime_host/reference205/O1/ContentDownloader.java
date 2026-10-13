package O1;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.util.Log;
import java.util.*;
import java.util.concurrent.*;

/** Keep the existing download screen open until both sets of game files are ready. */
public final class ContentDownloader {
 private static volatile boolean checking,downloading,failed,complete;
 private static volatile List<ExtraContent.Entry> pending=Collections.emptyList();
 private static final Set<ExtraContent.Entry> finished=Collections.synchronizedSet(new HashSet<ExtraContent.Entry>());
 private static int totalCount;private static long totalSize;
 public static void checkAssets(){
  checking=true;failed=false;complete=false;finished.clear();
  try {
   pending=ExtraContent.missing();CdnDownloader.checkAssets();
   totalCount=pending.size()+CdnDownloader.getTotalCount();totalSize=CdnDownloader.getTotalSize();
   for(ExtraContent.Entry e:pending)totalSize+=e.wireSize;
   Log.i("FFBE-Content","Missing extra files: "+pending.size()+"; total download bytes: "+totalSize);
  }catch(Exception e){failed=true;Log.e("FFBE-Content","Content check failed",e);}
  finally{checking=false;}
 }
 public static synchronized void startDownload(){
  if(downloading)return;downloading=true;
  new Thread(new Runnable(){public void run(){
   try {while(true){
    try{
     if(failed){if(!retry())return;checkAssets();continue;}
     final ResumableTransfer.Attempt attempt=new ResumableTransfer.Attempt();
     final Queue<List<ExtraContent.Entry>> queue=new ArrayDeque<>(ExtraContent.batches(ExtraContent.missing()));
     ExecutorService pool=Executors.newFixedThreadPool(4);
     if(CdnDownloader.getNeedsDownload())CdnDownloader.startDownload(attempt);
     for(int worker=0;worker<4;worker++)pool.submit(new Runnable(){public void run(){
      List<ExtraContent.Entry> batch;while((batch=attempt.next(queue))!=null){
       try{ExtraContent.downloadBatch(batch);finished.addAll(batch);}
       catch(Exception e){attempt.pause();Log.e("FFBE-Content","Content download paused: "+batch.get(0).path,e);return;}
      }
     }});
     pool.shutdown();while(!pool.awaitTermination(1,TimeUnit.SECONDS)){}
     while(CdnDownloader.getIsDownloading())Thread.sleep(200);
     if(ExtraContent.missing().isEmpty()&&!CdnDownloader.getNeedsDownload()){
      StoryPortTables.prepareIndexes();SideStoryTables.prepareIndexes();complete=true;
      Log.i("FFBE-Content","All content verified and ready");return;
     }
     if(!retry())return;
    }catch(Exception e){failed=true;Log.e("FFBE-Content","Download paused",e);if(!retry())return;checkAssets();}
   }}finally{downloading=false;}
  }},"FFBE-Content").start();
 }
 private static boolean retry(){
  final CountDownLatch latch=new CountDownLatch(1);final boolean[] again={false};
  try {
   final Activity activity=(Activity)Class.forName("com.square_enix.ffbejpn.Lapis").getMethod("getActivity").invoke(null);
   activity.runOnUiThread(new Runnable(){public void run(){
    if(activity.isFinishing()){latch.countDown();return;}
    new AlertDialog.Builder(activity).setTitle("Download paused")
     .setMessage("Your download progress has been saved. Check your connection and free storage space. Tap Resume to pick up where you left off.")
     .setCancelable(false).setPositiveButton("Resume",new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int w){again[0]=true;latch.countDown();}})
     .setNegativeButton("Close game",new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int w){activity.finishAndRemoveTask();latch.countDown();}}).show();
   }});latch.await();
  }catch(Exception e){Log.e("FFBE-Content","Cannot show download retry",e);}
  return again[0];
 }
 public static int getDownloadedCount(){return complete?totalCount:Math.min(totalCount,finished.size()+CdnDownloader.getDownloadedCount());}
 public static long getDownloadedSize(){if(complete)return totalSize;long n=CdnDownloader.getDownloadedSize();for(ExtraContent.Entry e:pending)n+=e.transferred;return Math.min(totalSize,n);}
 public static int getTotalCount(){return totalCount;}
 public static long getTotalSize(){return totalSize;}
 public static boolean getIsCheckingState(){return checking||CdnDownloader.getIsCheckingState();}
 public static boolean getIsDownloading(){return downloading;}
 public static boolean getNeedsDownload(){return !complete&&(failed||!pending.isEmpty()||CdnDownloader.getNeedsDownload());}
}
