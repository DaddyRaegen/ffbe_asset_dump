package O1;
import android.util.AtomicFile;
import java.io.*;
import java.util.*;
import java.security.MessageDigest;

/** Verified copies for the native player's fixed private-files movie names. */
public final class MovieAssets {
 private static File marker(String name)throws Exception{return new File(ExtraContent.files(),"game_assets/derived_movies/"+name+".tsv");}
 private static boolean owned(String name)throws Exception {
  try{String[] lines=new String(GameAssets.read(new AtomicFile(marker(name)).openRead(),4096),"UTF-8").split("\n",-1);String[] row=lines[1].split("\t",-1);return lines.length==3&&lines[0].equals("ffbe-derived-movie-v1")&&lines[2].isEmpty()&&row.length==3&&row[0].equals(name)&&row[1].matches("[a-f0-9]{64}")&&Long.parseLong(row[2])>0;}catch(Exception noMarker){return false;}
 }
 private static void record(String name,String hash,long size)throws Exception {
  File p=marker(name);if(!p.getParentFile().isDirectory()&&!p.getParentFile().mkdirs()&&!p.getParentFile().isDirectory())throw new IOException("Movie ownership directory unavailable");AtomicFile marker=new AtomicFile(p);FileOutputStream out=null;
  try{out=marker.startWrite();out.write(("ffbe-derived-movie-v1\n"+name+"\t"+hash+"\t"+size+"\n").getBytes("UTF-8"));marker.finishWrite(out);out=null;}finally{if(out!=null)marker.failWrite(out);}
 }
 static synchronized boolean prepare(String name,File source,String expected,String accepted)throws Exception {
  if(!name.matches("[A-Za-z0-9_-]+\\.usm")||!expected.matches("[a-f0-9]{64}")||source==null||!source.isFile()||source.length()<1||!expected.equals(ExtraContent.hash(source)))throw new IOException("Unverified selected movie source");
  File target=new File(ExtraContent.files(),name);long size=source.length();String previous=target.isFile()?ExtraContent.hash(target):"";
  if(target.isFile()&&target.length()==size&&previous.equals(expected)){record(name,expected,size);return true;}
  // Preserve an unfamiliar pre-existing movie. A known owned derived copy can
  // be repaired even when same-size corruption no longer matches its old hash.
  if(target.exists()&&!owned(name)&&!Arrays.asList(accepted.split(",",-1)).contains(previous))return false;
  AtomicFile output=new AtomicFile(target);FileOutputStream out=null;
  try{out=output.startWrite();MessageDigest digest=MessageDigest.getInstance("SHA-256");long written=0;try(InputStream in=new FileInputStream(source)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){out.write(b,0,n);digest.update(b,0,n);written+=n;}}out.getFD().sync();StringBuilder actual=new StringBuilder();for(byte b:digest.digest())actual.append(String.format(Locale.ROOT,"%02x",b&255));if(written!=size||out.getChannel().size()!=size||!expected.equals(actual.toString()))throw new IOException("Derived movie checksum mismatch");output.finishWrite(out);out=null;record(name,expected,size);return true;}finally{if(out!=null)output.failWrite(out);}
 }
}
