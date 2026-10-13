package O1;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

/** Uses a JVM-only URL handler for real HTTPS hostnames; production has no test-host exception. */
public class GithubTransferTest {
 static final String RELEASE="https://github.com/example/ffbe-content/releases/download/v4/content-01.bin";
 static final String ASSET="https://release-assets.githubusercontent.com/github-production-release-asset/fixture?sig=test";
 static byte[] container=new byte[200000];static List<Conn> connections=new ArrayList<>();static int checks,mode,bodies;static long progress,now;
 static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);checks++;}
 static class Conn extends HttpURLConnection {
  final int number;
  Conn(URL u){super(u);number=connections.size();connections.add(this);}
  public void connect(){}public void disconnect(){}public boolean usingProxy(){return false;}
  long[] range(){String[] p=getRequestProperty("Range").substring(6).split("-");return new long[]{Long.parseLong(p[0]),Long.parseLong(p[1])};}
  public int getResponseCode(){
   if(mode==16)return 403;
   if((mode==14||mode==15)&&number==0&&"release-assets.githubusercontent.com".equals(getURL().getHost()))return mode==14?403:401;
   if(mode==10)return 200;
   if(mode==8)return 302;
   if(mode==13&&number<4)return 307;
   if("github.com".equals(getURL().getHost()))return mode==12?308:302;
   return 206;
  }
  public String getHeaderField(String n){
   if(n.equals("Location")){
    if(mode==2)return "http://release-assets.githubusercontent.com/file";
    if(mode==3)return "https://release-assets.githubusercontent.com.evil.test/file";
    if(mode==4)return "https://user:secret@objects.githubusercontent.com/file";
    if(mode==5)return "https://objects.githubusercontent.com:444/file";
    if(mode==6)return "https://github.com/example/ffbe-content/releases/download/v4/other.bin";
    if(mode==7)return null;
    if(mode==9)return ASSET+"#unexpected";
    if(mode==12)return "https://objects.githubusercontent.com/fixture";
    return ASSET;
   }
   long[] r=range();
   if(n.equals("Content-Range"))return "bytes "+r[0]+"-"+r[1]+"/"+(mode==11?container.length+1:container.length);
   if(n.equals("Content-Length"))return Long.toString(r[1]-r[0]+1);
   return null;
  }
  public InputStream getInputStream(){bodies++;long[] r=range();byte[] b=Arrays.copyOfRange(container,(int)r[0],(int)r[1]+1);if(mode==1&&bodies==1)b=Arrays.copyOf(b,1234);return new ByteArrayInputStream(b);}
 }
 static Path fixture(Path root,int m)throws Exception{mode=m;connections.clear();bodies=0;progress=0;now=0;ResumableTransfer.clock=()->now;ResumableTransfer.clearRedirectCache();return Files.createTempDirectory(root,"github-").resolve("part");}
 static void fetch(String url,Path part,long offset,long size,long logicalSize)throws Exception{ResumableTransfer.fetch(url,part.toFile(),offset,size,logicalSize,n->progress=n);}
 static boolean fails(String url,Path part,long offset,long size,long total){try{fetch(url,part,offset,size,total);return false;}catch(Exception e){return true;}}
 public static void main(String[] args)throws Exception{
  Path root=Paths.get(args[0]);Files.createDirectories(root);new Random(33).nextBytes(container);
  URL.setURLStreamHandlerFactory(p->p.equals("https")?new URLStreamHandler(){protected URLConnection openConnection(URL u){return new Conn(u);}}:null);
  ResumableTransfer.delay=ms->{};
  String packed=RELEASE+"#ffbe-range=4000:100000:"+container.length;
  Path p=fixture(root,0);Files.write(p,Arrays.copyOfRange(container,4000,14000));fetch(packed,p,0,100000,100000);
  check(Arrays.equals(Files.readAllBytes(p),Arrays.copyOfRange(container,4000,104000)),"packed resume writes only exact logical file bytes");
  check(progress==100000&&connections.size()==2,"packed progress counts file bytes and follows one release redirect");
  for(Conn c:connections){check(c.getURL().getRef()==null,"packed fragment never sent to server");check("bytes=14000-103999".equals(c.getRequestProperty("Range")),"identical physical range retained at each redirect");check(c.getRequestProperty("Authorization")==null&&c.getRequestProperty("Cookie")==null,"no authorization or cookie headers sent");check(!c.getInstanceFollowRedirects(),"automatic unrestricted redirects disabled");}
  p=fixture(root,1);fetch(packed,p,0,100000,100000);check(connections.size()==3&&"bytes=5234-103999".equals(connections.get(2).getRequestProperty("Range")),"interrupted packed transfer reuses validated redirect and resumes physical offset plus preserved bytes");check(Arrays.equals(Files.readAllBytes(p),Arrays.copyOfRange(container,4000,104000)),"packed retry yields exact bytes");
  p=fixture(root,0);fetch(packed,p,5000,7000,100000);check(Arrays.equals(Files.readAllBytes(p),Arrays.copyOfRange(container,9000,16000)),"existing logical offsets compose with packed range without leaking neighbors");
  for(int m=2;m<=9;m++){p=fixture(root,m);Files.write(p,new byte[]{1,2,3});check(fails(packed,p,0,100000,100000),"unsafe or missing redirect rejected mode "+m);check(Files.size(p)==3&&bodies==0,"rejected redirect preserves partial without reading body "+m);check(connections.size()<=(m==8?5:1),"redirect failure bounded and never retried "+m);}
  p=fixture(root,10);check(fails(packed,p,0,100000,100000)&&bodies==0,"packed object full-response fallback rejected before reading");
  p=fixture(root,11);check(fails(packed,p,0,100000,100000)&&bodies==0,"container Content-Range total must match catalog exactly");
  p=fixture(root,12);fetch(packed,p,0,100000,100000);check(Arrays.equals(Files.readAllBytes(p),Arrays.copyOfRange(container,4000,104000)),"objects.githubusercontent.com HTTPS redirect supported");
  p=fixture(root,13);fetch(packed,p,0,100000,100000);check(connections.size()==5,"exactly four approved redirects allowed");
  String[] invalid={"-1:100000:200000","0:99999:200000","150000:100000:200000","0:100000:99999","0:0:200000","9223372036854775807:100000:9223372036854775807","0:100000:9223372036854775808","0:100000:200000:4","0%3A100000%3A200000"};
  for(String bounds:invalid){p=fixture(root,0);Files.write(p,new byte[]{7});check(fails(RELEASE+"#ffbe-range="+bounds,p,0,100000,100000)&&connections.isEmpty()&&Files.size(p)==1,"bad packed bounds rejected before network or partial mutation: "+bounds);}
  p=fixture(root,0);check(fails("https://example.test/file#ffbe-range=0:100000:200000",p,0,100000,100000)&&connections.isEmpty(),"packed fragment restricted to GitHub release source");
  p=fixture(root,8);check(fails("https://ffbe.luminest.io/downloads/base/file",p,0,100000,100000)&&connections.size()==1,"ordinary source redirects remain disallowed");
  p=fixture(root,10);fetch(RELEASE,p,0,container.length,container.length);check(Arrays.equals(Files.readAllBytes(p),container),"plain full-file HTTP200 behavior preserved");
  String second=RELEASE+"#ffbe-range=50000:100000:"+container.length;
  p=fixture(root,0);fetch(packed,p,0,100000,100000);connections.clear();now=119999;
  Path other=Files.createTempDirectory(root,"slice-").resolve("part");fetch(second,other,0,100000,100000);
  check(connections.size()==1&&connections.get(0).getURL().getHost().equals("release-assets.githubusercontent.com"),"different packed slices share the validated in-memory release redirect");
  check(Arrays.equals(Files.readAllBytes(other),Arrays.copyOfRange(container,50000,150000)),"cached redirect still requests and verifies the new slice's physical bounds");
  connections.clear();now=120000;other=Files.createTempDirectory(root,"expired-").resolve("part");fetch(second,other,0,100000,100000);
  check(connections.size()==2&&connections.get(0).getURL().getHost().equals("github.com"),"two-minute cache lifetime is fixed rather than extended by reads");
  for(int stale:new int[]{14,15}){
   p=fixture(root,0);fetch(packed,p,0,100000,100000);mode=stale;connections.clear();bodies=0;other=Files.createTempDirectory(root,"stale-").resolve("part");fetch(second,other,0,100000,100000);
   check(connections.size()==3&&connections.get(1).getURL().getHost().equals("github.com")&&bodies==1,"expired signed URL refreshes original exactly once after status "+(stale==14?403:401));
   check(Arrays.equals(Files.readAllBytes(other),Arrays.copyOfRange(container,50000,150000)),"refreshed signed URL keeps correct per-file bytes");
  }
  p=fixture(root,0);fetch(packed,p,0,100000,100000);mode=16;connections.clear();bodies=0;other=Files.createTempDirectory(root,"blocked-").resolve("part");
  check(fails(second,other,0,100000,100000)&&connections.size()==2&&bodies==0,"cached and original403 fails after one refresh without retry storm");
  mode=0;connections.clear();fetch(second,other,0,100000,100000);check(connections.size()==2&&connections.get(0).getURL().getHost().equals("github.com"),"rejected cached redirect is discarded before next Resume");
  p=fixture(root,3);check(fails(packed,p,0,100000,100000),"unapproved redirect rejected before cache insertion");mode=0;connections.clear();fetch(packed,p,0,100000,100000);check(connections.size()==2&&connections.get(0).getURL().getHost().equals("github.com"),"invalid redirect was never cached");
  System.out.println("PASSED "+checks+" GitHub redirect and packed-range checks");
 }
}
