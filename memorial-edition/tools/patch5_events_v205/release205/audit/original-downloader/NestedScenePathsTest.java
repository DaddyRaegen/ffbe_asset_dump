package O1;
import android.app.*;
import java.io.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Focused reference test: narrow path acceptance and original alias-copy behavior. */
public class NestedScenePathsTest {
 static int checks;
 static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);checks++;}
 static String hash(byte[] bytes)throws Exception{StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))s.append(String.format("%02x",b&255));return s.toString();}
 static String row(String name,String h,int size){return name+"\t"+h+"\t"+size+"\thttps://github.com/example/content/releases/download/pinned/new-scenes.bin#ffbe-range=100:"+size+":1000\t0\t"+size+"\t0\t"+size+"\n";}
 static void clear(Class<?> owner,String field)throws Exception{Field f=owner.getDeclaredField(field);f.setAccessible(true);f.set(null,null);}
 static void reject(String name,String h,int size)throws Exception{boolean rejected=false;try{new ExtraContent.Entry(row(name,h,size).trim().split("\t",-1));}catch(IOException e){rejected=true;}check(rejected,"reject unsupported/traversing nested path: "+name);}
 public static void main(String[] args)throws Exception {
  Path root=Files.createTempDirectory(Paths.get(args[0]),"scene-paths-");Path assets=root.resolve("assets"),files=root.resolve("files");Files.createDirectories(assets.resolve("side_stories"));Files.createDirectories(files);
  ActivityThread.app=new Application(files.toFile(),assets.toFile());
  byte[] bytes="original verified cached scene".getBytes("UTF-8");String h=hash(bytes),jp="r2_scene_jp/05536d814e633e15/733080804.cpk",gl="r2_scene_gl/1a741196ad6bec00/845040101.cpk";
  for(String name:new String[]{"side_stories/original.cpk","side_stories/"+jp,"side_stories/"+gl}){new ExtraContent.Entry(row(name,h,bytes.length).trim().split("\t",-1));check(true,"admit original/qualified JP/GL scene path");}
  for(String name:new String[]{"side_stories/r2_scene_us/05536d814e633e15/a.cpk","side_stories/r2_scene_jp/05536d814e633e1/a.cpk","side_stories/r2_scene_jp/05536d814e633e15/a.dat","side_stories/r2_scene_jp/05536d814e633e15/../a.cpk","side_stories/r2_scene_jp/05536d814e633e15/x/a.cpk","battle/r2_scene_jp/05536d814e633e15/a.cpk","side_stories/../a.cpk"})reject(name,h,bytes.length);
  Files.write(assets.resolve("content_delivery.tsv"),("ffbe-content-v1\n"+row("side_stories/original.cpk",h,bytes.length)+row("side_stories/"+jp,h,bytes.length)+row("side_stories/"+gl,h,bytes.length)).getBytes("UTF-8"));
  Files.write(assets.resolve("side_stories/manifest.tsv"),("original.cpk\t"+h+"\t\n"+jp+"\t"+h+"\t\n"+gl+"\t"+h+"\t\n").getBytes("UTF-8"));
  ExtraContent.Entry flat=new ExtraContent.Entry(row("side_stories/original.cpk",h,bytes.length).trim().split("\t",-1));File cached=ExtraContent.target(flat);cached.getParentFile().mkdirs();Files.write(cached.toPath(),bytes);
  check(ExtraContent.missing().isEmpty(),"all nested aliases reuse the original verified cache");
  for(String nested:new String[]{jp,gl}){String chosen=SideStoryTables.choose(nested,null);check(chosen!=null&&Arrays.equals(bytes,Files.readAllBytes(Paths.get(chosen))),"nested alias parent directories and exact original bytes prepared");check(Paths.get(chosen).startsWith(files.resolve("side_stories/"+h)),"nested destination stays in original hash cache");}
  Path existing=root.resolve("unknown.cpk");byte[] unknown="future independent source".getBytes("UTF-8");Files.write(existing,unknown);check(existing.toString().equals(SideStoryTables.choose(jp,existing.toString())),"unknown original source remains authoritative");
  check("preserved".equals(SideStoryTables.choose("../escape.cpk","preserved")),"invalid SideStory name returns original fallback");
  byte[] bundled="original bundled priority".getBytes("UTF-8");Files.write(assets.resolve("side_stories/original.cpk"),bundled);try(InputStream in=ExtraContent.open("side_stories/original.cpk")){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[32];int n;while((n=in.read(b))!=-1)out.write(b,0,n);check(Arrays.equals(bundled,out.toByteArray()),"original bundled-first open behavior preserved");}
  Files.write(assets.resolve("side_stories/manifest.tsv"),("new.dat\t"+h+"\t"+h+"\n").getBytes("UTF-8"));clear(SideStoryTables.class,"entries");check(SideStoryTables.choose("new.dat",null)==null,"original missing DAT with expected source remains fallback");
  System.out.println("PASSED "+checks+" narrow nested scene path and original behavior checks");
 }
}
