package O1;
import android.app.*;
import java.nio.file.*;
import java.lang.reflect.*;
import java.io.*;
import java.net.*;

public final class BaseCacheIntegrityTest {
 static int checks,network;
 static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);checks++;}
 public static void main(String[] args)throws Exception {
  Path root=Files.createTempDirectory(Paths.get(args[0]),"integrity-");Path assets=root.resolve("assets"),files=root.resolve("files");Files.createDirectories(assets);Files.createDirectories(files);
  ActivityThread.app=new Application(files.toFile(),assets.toFile());
  URL.setURLStreamHandlerFactory(p->p.equals("https")?new URLStreamHandler(){protected URLConnection openConnection(URL u)throws IOException{network++;throw new IOException("offline fixture");}}:null);
  byte[] good={1,2,3,4},bad={1,2,3,5};String hash=DeliveryPolicy.hash(good);
  Files.write(assets.resolve("base_delivery.tsv"),("ffbe-base-v1\non_demand_asset\tcached.dat\t4\t"+hash+"\thttps://ffbe.luminest.io/downloads/base/v1/"+hash+".bin\n").getBytes("UTF-8"));
  CdnDownloader.initLocalDir();Field f=CdnDownloader.class.getDeclaredField("localAssetDir");f.setAccessible(true);
  Path dest=Paths.get((String)f.get(null),"on_demand_asset/199/199/assets/cached.dat");Files.createDirectories(dest.getParent());Files.write(dest,bad);
  CdnDownloader.checkAssets();check(CdnDownloader.getNeedsDownload()&&CdnDownloader.getTotalCount()==1,"same-size corrupt inherited cache keeps native download gate closed");check(network==0,"offline integrity check needs no network");
  Files.write(dest,good);CdnDownloader.checkAssets();check(!CdnDownloader.getNeedsDownload()&&CdnDownloader.getTotalCount()==0,"valid inherited Patch5 or v201 cache is reused");check(network==0,"valid warm cache is usable offline");
  System.out.println("PASSED "+checks+" inherited base cache integrity checks");
 }
}
