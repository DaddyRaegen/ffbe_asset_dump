package O1;
import android.app.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.lang.reflect.*;
import java.security.*;
import java.util.*;
import java.util.zip.*;

public class PackedExtraContentTest {
 static byte[] container;static int requests,checks;static List<String> ranges=new ArrayList<>();
 static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);checks++;}
 static String hash(byte[] b)throws Exception{StringBuilder s=new StringBuilder();for(byte n:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format("%02x",n&255));return s.toString();}
 static class Conn extends HttpURLConnection {
  Conn(URL u){super(u);requests++;}public void connect(){}public void disconnect(){}public boolean usingProxy(){return false;}
  long[] bounds(){String[] p=getRequestProperty("Range").substring(6).split("-");return new long[]{Long.parseLong(p[0]),Long.parseLong(p[1])};}
  public int getResponseCode(){return getURL().getHost().equals("github.com")?302:206;}
  public String getHeaderField(String s){if(s.equals("Location"))return "https://release-assets.githubusercontent.com/public-fixture";long[] b=bounds();return s.equals("Content-Range")?"bytes "+b[0]+"-"+b[1]+"/"+container.length:null;}
  public InputStream getInputStream(){long[] b=bounds();ranges.add(getRequestProperty("Range"));return new ByteArrayInputStream(Arrays.copyOfRange(container,(int)b[0],(int)b[1]+1));}
 }
 static void reset()throws Exception{for(String n:new String[]{"entries","byHash"}){Field f=ExtraContent.class.getDeclaredField(n);f.setAccessible(true);f.set(null,null);}Field f=ExtraContent.class.getDeclaredField("verified");f.setAccessible(true);((Map<?,?>)f.get(null)).clear();}
 public static void main(String[] args)throws Exception{
  Path root=Files.createTempDirectory(Paths.get(args[0]),"packed-extra-");Files.createDirectories(root.resolve("assets"));Files.createDirectories(root.resolve("files/content_delivery"));ActivityThread.app=new Application(root.resolve("files").toFile(),root.resolve("assets").toFile());
  URL.setURLStreamHandlerFactory(p->p.equals("https")?new URLStreamHandler(){protected URLConnection openConnection(URL u){return new Conn(u);}}:null);ResumableTransfer.delay=ms->{};
  byte[] plain=new byte[65536];new Random(91).nextBytes(plain);ByteArrayOutputStream out=new ByteArrayOutputStream();Deflater d=new Deflater(6,true);try(DeflaterOutputStream zip=new DeflaterOutputStream(out,d)){zip.write(plain);}finally{d.end();}byte[] wire=out.toByteArray();
  int start=7000;container=new byte[start+wire.length+9000];Arrays.fill(container,(byte)33);System.arraycopy(wire,0,container,start,wire.length);
  String h=hash(plain),base="https://github.com/example/ffbe-content/releases/download/v4/extras-01.bin",url=base+"#ffbe-range="+start+":"+wire.length+":"+container.length;
  String row="encyclopedia/packed.dat\t"+h+"\t"+plain.length+"\t"+url+"\t0\t"+wire.length+"\t8\t"+wire.length+"\n";
  Path manifest=root.resolve("assets/content_delivery.tsv");Files.write(manifest,("ffbe-content-v1\n"+row+row.replace("encyclopedia/packed.dat","side_stories/alias.dat")).getBytes("UTF-8"));
  Path partial=root.resolve("files/content_delivery/"+h+".part");Files.write(partial,Arrays.copyOf(wire,10000));
  List<ExtraContent.Entry> missing=ExtraContent.missing();check(missing.size()==1&&missing.get(0).transferred==10000,"packed extra deduplicates aliases and reuses preexisting compressed partial");
  List<List<ExtraContent.Entry>> batches=ExtraContent.batches(missing);ExtraContent.downloadBatch(batches.get(0));
  check(requests==2&&ranges.get(0).equals("bytes=17000-"+(start+wire.length-1)),"packed extra resumes through approved redirect at exact physical byte");
  check(Arrays.equals(plain,Files.readAllBytes(ExtraContent.target(missing.get(0)).toPath())),"only packed compressed slice is unpacked and SHA-256 verified");
  check(!Files.exists(partial)&&ExtraContent.missing().isEmpty(),"verified extra finalizes and removes its completed partial");
  reset();Files.write(manifest,("ffbe-content-v1\n"+row.replace(url,"https://ffbe.luminest.io/downloads/content/"+h+".bin")).getBytes("UTF-8"));check(ExtraContent.missing().isEmpty()&&requests==2,"completed extra cache survives switching between packed and original URL");
  reset();Files.write(manifest,("ffbe-content-v1\n"+row.replace("ffbe-range="+start+":"+wire.length,"ffbe-range="+start+":"+(wire.length-1))).getBytes("UTF-8"));boolean rejected=false;try{ExtraContent.missing();}catch(IOException e){rejected=true;}check(rejected&&requests==2,"invalid packed wire size rejected while parsing catalog");
  System.out.println("PASSED "+checks+" packed extra-content checks");
 }
}
