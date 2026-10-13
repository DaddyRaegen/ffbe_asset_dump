package O1;
import android.app.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.lang.reflect.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.*;

public class BaseTest {
 static byte[] data=new byte[131072];static volatile int mode,requests;static int checks;static List<Long> starts=Collections.synchronizedList(new ArrayList<Long>());
 static CountDownLatch active,release;
 static void check(boolean ok,String s){if(!ok)throw new AssertionError(s);checks++;}
 static String hash(byte[] b)throws Exception{StringBuilder s=new StringBuilder();for(byte n:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format("%02x",n&255));return s.toString();}
 static class Conn extends HttpURLConnection {
  Conn(URL u){super(u);synchronized(BaseTest.class){requests++;}}public void connect(){}public void disconnect(){}public boolean usingProxy(){return false;}
  long[] bounds(){String[] p=getRequestProperty("Range").substring(6).split("-");return new long[]{Long.parseLong(p[0]),Long.parseLong(p[1])};}
  public int getResponseCode()throws IOException{
   if(mode==1)throw new IOException("offline");if(mode==3)return 403;
   if(mode==4){active.countDown();try{if(!release.await(10,TimeUnit.SECONDS))throw new IOException("test timed out");}catch(InterruptedException e){throw new IOException(e);}}
   return 206;
  }
  public String getHeaderField(String name){long[] b=bounds();return name.equals("Content-Range")?"bytes "+b[0]+"-"+b[1]+"/"+data.length:null;}
  public InputStream getInputStream(){long[] b=bounds();starts.add(b[0]);byte[] out=Arrays.copyOfRange(data,(int)b[0],(int)b[1]+1);if(mode==2)out[0]^=1;return new ByteArrayInputStream(out);}
 }
 static void waitDone()throws Exception{long end=System.currentTimeMillis()+10000;while(CdnDownloader.getIsDownloading()&&System.currentTimeMillis()<end)Thread.sleep(5);check(!CdnDownloader.getIsDownloading(),"download worker completes");}
 public static void main(String[] args)throws Exception {
  new Random(9).nextBytes(data);Path root=Files.createTempDirectory(Paths.get(args[0]),"base-");Files.createDirectories(root.resolve("assets"));Files.createDirectories(root.resolve("files"));
  ActivityThread.app=new Application(root.resolve("files").toFile(),root.resolve("assets").toFile());
  URL.setURLStreamHandlerFactory(p->p.equals("https")?new URLStreamHandler(){protected URLConnection openConnection(URL u){return new Conn(u);}}:null);ResumableTransfer.delay=ms->{};
  String h=hash(data),row="on_demand_asset\ta.dat\t"+data.length+"\t"+h+"\thttps://ffbe.luminest.io/downloads/base/v1/"+h+".bin\n";
  Path manifest=root.resolve("assets/base_delivery.tsv");Files.write(manifest,("ffbe-base-v1\n"+row).getBytes("UTF-8"));
  CdnDownloader.checkAssets();check(CdnDownloader.getTotalCount()==1&&requests==0,"catalog is usable without a manifest network request");
  Field field=CdnDownloader.class.getDeclaredField("localAssetDir");field.setAccessible(true);Path dest=Paths.get((String)field.get(null),"on_demand_asset/199/199/assets/a.dat");Files.createDirectories(dest.getParent());Path part=Paths.get(dest+".tmp");Files.write(part,Arrays.copyOf(data,32768));
  CdnDownloader.checkAssets();check(CdnDownloader.getDownloadedSize()==32768,"saved partial progress appears on next check");mode=1;CdnDownloader.startDownload();waitDone();check(CdnDownloader.getNeedsDownload()&&Files.size(part)==32768&&!Files.exists(dest),"failed worker preserves partial and keeps game download gate closed");
  mode=0;requests=0;CdnDownloader.startDownload();waitDone();check(starts.get(0)==32768&&Arrays.equals(data,Files.readAllBytes(dest)),"base file resumes and verifies final bytes");check(!CdnDownloader.getNeedsDownload()&&CdnDownloader.getDownloadedCount()==1&&CdnDownloader.getDownloadedSize()==data.length,"success counters accurate");
  CdnDownloader.checkAssets();check(CdnDownloader.getTotalCount()==0&&!CdnDownloader.getNeedsDownload(),"existing completed cache reused");
  Files.delete(dest);mode=2;CdnDownloader.checkAssets();CdnDownloader.startDownload();waitDone();check(!Files.exists(dest)&&CdnDownloader.getNeedsDownload(),"wrong checksum never publishes game data or reports success");
  mode=0;CdnDownloader.startDownload();waitDone();check(Files.exists(dest)&&!CdnDownloader.getNeedsDownload(),"retry repairs rejected corrupt transfer");
  StringBuilder many=new StringBuilder("ffbe-base-v1\n");
  for(int i=0;i<32;i++)many.append(row.replace("a.dat","queue-"+i+".dat"));
  Files.write(manifest,many.toString().getBytes("UTF-8"));
  Path saved=dest.resolveSibling("queue-0.dat.tmp");Files.write(saved,Arrays.copyOf(data,32768));
  mode=3;requests=0;CdnDownloader.checkAssets();CdnDownloader.startDownload();waitDone();
  check(requests>=1&&requests<=4,"terminal HTTP failure stops the queue within the four admitted transfers");
  check(Files.size(saved)==32768&&CdnDownloader.getNeedsDownload(),"queue pause preserves partial data and keeps the download gate closed");
  ResumableTransfer.Attempt attempt=new ResumableTransfer.Attempt();
  active=new CountDownLatch(4);release=new CountDownLatch(1);mode=4;requests=0;
  CdnDownloader.startDownload(attempt);check(active.await(5,TimeUnit.SECONDS),"four real base transfers are in flight");
  attempt.pause();release.countDown();waitDone();
  check(requests==4&&CdnDownloader.getDownloadedCount()==4,"a shared extra-file failure lets admitted base transfers finish without starting queued ones");
  check(CdnDownloader.getNeedsDownload(),"unstarted work still requires download after the shared pause");
  mode=0;requests=0;CdnDownloader.startDownload();waitDone();
  check(requests==28&&CdnDownloader.getDownloadedCount()==32&&!CdnDownloader.getNeedsDownload(),"Resume rebuilds the queue and reuses the four completed transfers");
  for(int i=0;i<32;i++)check(Arrays.equals(data,Files.readAllBytes(dest.resolveSibling("queue-"+i+".dat"))),"resumed queued file has exact bytes");
  String release="https://github.com/example/ffbe-content/releases/download/v4/base-01.bin";
  Files.write(manifest,("ffbe-base-v1\n"+row.replace("https://ffbe.luminest.io/downloads/base/v1/"+h+".bin",release+"#ffbe-range=0:"+data.length+":"+data.length)).getBytes("UTF-8"));
  requests=0;CdnDownloader.checkAssets();check(!CdnDownloader.getNeedsDownload()&&requests==0,"changing delivery host reuses the completed base cache");
  byte[] slice=Arrays.copyOfRange(data,5000,65000);String sliceHash=hash(slice);
  Files.write(manifest,("ffbe-base-v1\non_demand_asset\tpacked.dat\t60000\t"+sliceHash+"\t"+release+"#ffbe-range=5000:60000:"+data.length+"\n").getBytes("UTF-8"));
  Path packedPart=dest.resolveSibling("packed.dat.tmp");Files.write(packedPart,Arrays.copyOf(slice,20000));starts.clear();CdnDownloader.checkAssets();CdnDownloader.startDownload();waitDone();
  check(starts.get(0)==25000&&Arrays.equals(slice,Files.readAllBytes(dest.resolveSibling("packed.dat"))),"packed base transfer preserves existing partial and validates logical-file hash");
  Files.write(manifest,"invalid\n".getBytes("UTF-8"));boolean failed=false;try{CdnDownloader.checkAssets();}catch(Exception e){failed=true;}check(failed&&CdnDownloader.getNeedsDownload(),"catalog errors remain blocking instead of silently entering game");
  System.out.println("PASSED "+checks+" base cache and recovery checks");
 }
}
