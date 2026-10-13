package O1;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class TransferTest {
 static byte[] source=new byte[131072];static int requests,mode;static List<Long> starts=new ArrayList<>(),waits=new ArrayList<>();static long progress;static int checks;
 static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);checks++;}
 static class Conn extends HttpURLConnection {
  final int attempt;
  Conn(URL u){super(u);attempt=++requests;}
  public void connect(){}public void disconnect(){}public boolean usingProxy(){return false;}
  long[] range(){String[] a=getRequestProperty("Range").substring(6).split("-");return new long[]{Long.parseLong(a[0]),Long.parseLong(a[1])};}
  public int getResponseCode()throws IOException{
   if(mode==2)throw new IOException("offline");
   if(mode==3&&attempt==1)return 429;
   if(mode==4)return 200;
   if(mode==7)return 404;
   return 206;
  }
  public String getHeaderField(String name){long[] r=range();
   if(name.equals("Retry-After"))return "7";
   if(name.equals("Content-Range"))return "bytes "+(mode==5?r[0]+1:r[0])+"-"+r[1]+"/"+source.length;
   if(name.equals("Content-Length"))return Long.toString(r[1]-r[0]+1);
   return null;
  }
  public InputStream getInputStream(){long[] r=range();starts.add(r[0]);byte[] bytes=Arrays.copyOfRange(source,(int)r[0],(int)r[1]+1);
   if(mode==1&&attempt==1)bytes=Arrays.copyOf(bytes,32768);
   if(mode==6)bytes=Arrays.copyOf(bytes,Math.min(bytes.length/2,4096));
   return new ByteArrayInputStream(bytes);
  }
 }
 static void fetch(Path file)throws Exception {ResumableTransfer.fetch("https://example.test/file",file.toFile(),0,source.length,source.length,n->progress=n);}
 static boolean fails(Path f){try{fetch(f);return false;}catch(Exception e){return true;}}
 static Path fixture(Path root,int m)throws Exception{mode=m;requests=0;progress=0;starts.clear();waits.clear();return Files.createTempDirectory(root,"transfer-").resolve("file.tmp");}
 public static void main(String[] args)throws Exception {
  new Random(7).nextBytes(source);Path root=Paths.get(args[0]);Files.createDirectories(root);
  URL.setURLStreamHandlerFactory(p->p.equals("https")?new URLStreamHandler(){protected URLConnection openConnection(URL u){return new Conn(u);}}:null);
  ResumableTransfer.delay=ms->waits.add(ms);
  Path p=fixture(root,1);fetch(p);check(requests==2&&starts.get(1)==32768,"automatic retry resumes at exact saved offset");check(Arrays.equals(source,Files.readAllBytes(p)),"resumed bytes match original");check(progress==source.length,"retry progress is not double counted");
  p=fixture(root,2);Files.write(p,Arrays.copyOf(source,50000));check(fails(p),"offline failure reported");check(Files.size(p)==50000&&progress==50000,"existing partial and displayed progress survive failure");
  mode=0;requests=0;fetch(p);check(starts.get(0)==50000,"new invocation resumes saved bytes after restart");check(Arrays.equals(source,Files.readAllBytes(p)),"restart final bytes correct");
  p=fixture(root,3);fetch(p);check(requests==2&&waits.get(0)>=7000,"rate limit honors Retry-After");
  p=fixture(root,4);Files.write(p,Arrays.copyOf(source,1000));check(fails(p)&&Files.size(p)==1000&&starts.isEmpty(),"ignored resume ranges never append a full response");
  p=fixture(root,5);check(fails(p)&&!Files.exists(p),"wrong Content-Range rejected before writing");
  p=fixture(root,6);check(fails(p)&&Files.size(p)==5*4096,"all interrupted attempts preserve newly received bytes");mode=0;requests=0;fetch(p);check(Arrays.equals(source,Files.readAllBytes(p)),"subsequent retry finishes accumulated partial");
  p=fixture(root,7);check(fails(p)&&requests==1,"missing files fail without a retry storm");
  p=fixture(root,0);Files.write(p,source);fetch(p);check(requests==0,"finished partial requires no repeat network request");
  p=fixture(root,0);Files.write(p,new byte[source.length+1]);fetch(p);check(Arrays.equals(source,Files.readAllBytes(p)),"oversized stale partial safely restarts");
  System.out.println("PASSED "+checks+" transfer recovery checks");
 }
}
