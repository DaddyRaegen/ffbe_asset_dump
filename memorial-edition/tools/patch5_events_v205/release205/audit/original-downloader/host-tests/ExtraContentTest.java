package O1;
import android.app.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.lang.reflect.*;
import java.security.*;
import java.util.*;
import java.util.zip.*;

public class ExtraContentTest {
 static byte[] archive;static int mode,requests,checks;static List<String> ranges=new ArrayList<>();static Path root;
 static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);checks++;}
 static String hash(byte[] b)throws Exception{StringBuilder s=new StringBuilder();for(byte n:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format("%02x",n&255));return s.toString();}
 static class Conn extends HttpURLConnection {
  Conn(URL u){super(u);requests++;}
  public void connect(){} public void disconnect(){}public boolean usingProxy(){return false;}
  long[] bounds(){String[] p=getRequestProperty("Range").substring(6).split("-");return new long[]{Long.parseLong(p[0]),Long.parseLong(p[1])};}
  public int getResponseCode()throws IOException{if(mode==4)throw new IOException("offline");return mode==1?200:206;}
  public String getHeaderField(String s){if(!s.equals("Content-Range"))return null;long[] b=bounds();return "bytes "+b[0]+"-"+b[1]+"/"+(mode==5?archive.length+1:archive.length);}
  public InputStream getInputStream(){long[] b=bounds();ranges.add(getRequestProperty("Range"));byte[] data=Arrays.copyOfRange(archive,(int)b[0],(int)b[1]+1);if(mode==2)data=Arrays.copyOf(data,data.length/2);if(mode==3)data[data.length/2]^=0x7f;return new ByteArrayInputStream(data);}
 }
 static void reset()throws Exception{
  for(String n:new String[]{"entries","byHash"}){Field f=ExtraContent.class.getDeclaredField(n);f.setAccessible(true);f.set(null,null);}
  Field f=ExtraContent.class.getDeclaredField("verified");f.setAccessible(true);((Map<?,?>)f.get(null)).clear();
 }
 static List<ExtraContent.Entry> fixture(String label)throws Exception{
  reset();mode=0;requests=0;ranges.clear();root=Files.createTempDirectory(root.getParent(),label);
  Files.createDirectories(root.resolve("assets"));Files.createDirectories(root.resolve("files"));
  ActivityThread.app=new Application(root.resolve("files").toFile(),root.resolve("assets").toFile());
  byte[] a="First archive payload".getBytes("UTF-8"),b="Second translated scene\nwide comma\uFF0Cno extra space".getBytes("UTF-8");
  ByteArrayOutputStream encoded=new ByteArrayOutputStream();Deflater deflater=new Deflater(6,true);try(DeflaterOutputStream d=new DeflaterOutputStream(encoded,deflater)){d.write(b);}finally{deflater.end();}
  byte[] compressed=encoded.toByteArray();archive=new byte[19+a.length+27+compressed.length+5];Arrays.fill(archive,(byte)12);
  int ao=19,bo=19+a.length+27;System.arraycopy(a,0,archive,ao,a.length);System.arraycopy(compressed,0,archive,bo,compressed.length);
  String url="https://ffbe.luminest.io/downloads/beta/fixture.apk";
  String one="side_stories/a.cpk\t"+hash(a)+"\t"+a.length+"\t"+url+"\t"+ao+"\t"+a.length+"\t0\t"+archive.length;
  String two="side_stories/b.cpk\t"+hash(b)+"\t"+b.length+"\t"+url+"\t"+bo+"\t"+compressed.length+"\t8\t"+archive.length;
  Files.write(root.resolve("assets/content_delivery.tsv"),("ffbe-content-v1\n"+one+"\n"+two+"\n"+one.replace("side_stories/a.cpk","story_ports/alias.cpk")+"\n").getBytes("UTF-8"));
  List<ExtraContent.Entry> es=ExtraContent.missing();check(es.size()==2,"deduplicate identical bytes across asset names");return es;
 }
 static void failDownload(ExtraContent.Entry e)throws Exception{boolean failed=false;try{ExtraContent.download(e);}catch(Exception expected){failed=true;}check(failed,"bad download rejected");check(!ExtraContent.target(e).exists(),"bad bytes never published to game");}
 public static void main(String[] args)throws Exception{
  root=Paths.get(args[0],"seed");Files.createDirectories(root.getParent());
  ResumableTransfer.delay=ms->{};
  URL.setURLStreamHandlerFactory(p->p.equals("https")?new URLStreamHandler(){protected URLConnection openConnection(URL u){return new Conn(u);}}:null);
  List<ExtraContent.Entry> es=fixture("fresh-");
  boolean missing=false;try{ExtraContent.open("side_stories/a.cpk");}catch(FileNotFoundException e){missing=true;}
  check(missing&&requests==0,"game reads do not initiate network requests");
  List<List<ExtraContent.Entry>> batches=ExtraContent.batches(es);check(batches.size()==1,"adjacent archives share one HTTP request");
  ExtraContent.downloadBatch(batches.get(0));check(requests==1,"one exact-range request for adjacent files");
  check(ExtraContent.missing().isEmpty(),"fresh download complete");
  for(ExtraContent.Entry e:es)check(ExtraContent.hash(ExtraContent.target(e)).equals(e.hash),"download hash verified");
  try(InputStream in=ExtraContent.open("story_ports/alias.cpk")){check(in.read()!=-1,"alias reuses downloaded bytes");}
  reset();mode=4;check(ExtraContent.missing().isEmpty()&&requests==1,"cached content remains available offline after restart");
  // The same installed catalogue needs no repeat downloads; one changed hash requests only that file.
  Path manifest=root.resolve("assets/content_delivery.tsv");String text=new String(Files.readAllBytes(manifest),"UTF-8");text=text.replace(es.get(1).hash,hash("new revision".getBytes("UTF-8")));Files.write(manifest,text.getBytes("UTF-8"));reset();
  check(ExtraContent.missing().size()==1,"incremental update requests only changed content");
  es=fixture("reuse-");File old=ExtraContent.target(es.get(0));old.getParentFile().mkdirs();Files.write(old.toPath(),Arrays.copyOfRange(archive,(int)es.get(0).offset,(int)(es.get(0).offset+es.get(0).wireSize)));
  check(ExtraContent.missing().size()==1&&requests==0,"old full-APK cache reused without network");
  es=fixture("resume-");ExtraContent.Entry e=es.get(0);mode=2;failDownload(e);Path part=root.resolve("files/content_delivery/"+e.hash+".part");long have=Files.size(part);check(have>0&&have<e.wireSize,"interrupted download retained");
  mode=0;ExtraContent.download(e);check(ranges.get(ranges.size()-1).startsWith("bytes="+(e.offset+have)+"-"),"retry resumes after received bytes");check(!Files.exists(part),"partial removed after success");
  es=fixture("ignored-");mode=1;failDownload(es.get(0));check(ranges.isEmpty(),"full APK response rejected before reading its body");
  es=fixture("wrongrange-");mode=5;failDownload(es.get(0));
  es=fixture("corrupt-");mode=3;failDownload(es.get(0));check(!Files.exists(root.resolve("files/content_delivery/"+es.get(0).hash+".part")),"corrupt compressed bytes removed for clean retry");mode=0;ExtraContent.download(es.get(0));check(ExtraContent.target(es.get(0)).exists(),"retry repairs corrupted download");
  es=fixture("batchinterrupted-");mode=2;boolean threw=false;try{ExtraContent.downloadBatch(ExtraContent.batches(es).get(0));}catch(Exception expected){threw=true;}check(threw,"interrupted batch reports failure");mode=0;for(List<ExtraContent.Entry> batch:ExtraContent.batches(ExtraContent.missing()))ExtraContent.downloadBatch(batch);check(ExtraContent.missing().isEmpty(),"interrupted batch resumes remaining content");
  es=fixture("invalid-");manifest=root.resolve("assets/content_delivery.tsv");text=new String(Files.readAllBytes(manifest),"UTF-8").replace("side_stories/a.cpk","side_stories/../a.cpk");Files.write(manifest,text.getBytes("UTF-8"));reset();threw=false;try{ExtraContent.missing();}catch(Exception expected){threw=true;}check(threw,"unsafe manifest paths rejected");
  System.out.println("PASSED "+checks+" content delivery checks");
 }
}
