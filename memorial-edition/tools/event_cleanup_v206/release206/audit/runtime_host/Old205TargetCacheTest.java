package O1;
import android.app.*;
import java.io.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Exercise actual v205 targets against v206 metadata inside disposable owned files. */
public class Old205TargetCacheTest {
 static int checks;
 static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);checks++;}
 static String hash(byte[] bytes)throws Exception{StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))s.append(String.format("%02x",b&255));return s.toString();}
 @SuppressWarnings("unchecked") static Map<String,ExtraContent.Entry> loaded()throws Exception{Field f=ExtraContent.class.getDeclaredField("entries");f.setAccessible(true);return (Map<String,ExtraContent.Entry>)f.get(null);}
 public static void main(String[] args)throws Exception{
  Path payload=Paths.get(args[0]),baseline=Paths.get(args[1]),fixtures=Paths.get(args[2]),requirements=Paths.get(args[3]);
  Path root=Files.createTempDirectory(fixtures,"old205-targets-");Path files=root.resolve("files"),assets=root.resolve("assets");
  Files.createDirectories(files);Files.createDirectories(assets.resolve("side_stories"));
  Files.copy(payload.resolve("content_delivery.tsv"),assets.resolve("content_delivery.tsv"));
  Files.copy(payload.resolve("side_stories/manifest.tsv"),assets.resolve("side_stories/manifest.tsv"));
  Files.copy(baseline.resolve("base_delivery.tsv"),assets.resolve("base_delivery.tsv"));
  ActivityThread.app=new Application(files.toFile(),assets.toFile());ExtraContent.load();Map<String,ExtraContent.Entry> entries=loaded();
  byte[] saved="isolated progress retained across event cleanup".getBytes("UTF-8");Path save=files.resolve("profile.save");Files.write(save,saved);
  int changed=0;
  for(String line:Files.readAllLines(requirements.resolve("old205-targets.tsv"),java.nio.charset.StandardCharsets.UTF_8)){
   if(line.isEmpty())continue;String[] p=line.split("\t",-1);check(p.length==7,"complete cache provenance record");
   String path=p[0],leaf=path.substring("side_stories/".length());byte[] before=Files.readAllBytes(Paths.get(p[1])),after=Files.readAllBytes(Paths.get(p[2]));
   ExtraContent.Entry entry=entries.get(path);check(entry!=null&&entry.hash.equals(p[4]),"actual206 cache entry admitted");
   check(hash(before).equals(p[3])&&hash(after).equals(p[4])&&after.length==entry.size,"old/new source blobs match both signed metadata pins");
   Path oldTarget=files.resolve(p[5]),newTarget=ExtraContent.target(entry).toPath();check(newTarget.equals(files.resolve(p[6])),"v206 target uses inherited original hash/path layout");
   Files.createDirectories(oldTarget.getParent());Files.write(oldTarget,before);Files.createDirectories(newTarget.getParent());Files.write(newTarget,after);
   String chosen=SideStoryTables.choose(leaf,oldTarget.toString());check(newTarget.toString().equals(chosen),"old205 target refreshes to the exact cached206 object");
   check(Arrays.equals(before,Files.readAllBytes(oldTarget))&&Arrays.equals(after,Files.readAllBytes(newTarget)),"refresh preserves original and new cache bytes");
   check(!ExtraContent.missing().stream().anyMatch(e->e.hash.equals(entry.hash)),"verified refreshed206 object omitted from original missing queue");
   // Unknown original data remains authoritative rather than being overwritten.
   Path unknown=files.resolve("unknown-"+changed+".dat");byte[] arbitrary=("unknown original"+changed).getBytes("UTF-8");Files.write(unknown,arbitrary);
   check(unknown.toString().equals(SideStoryTables.choose(leaf,unknown.toString())),"unrecognized source remains authoritative");
   check(Arrays.equals(arbitrary,Files.readAllBytes(unknown)),"unrecognized original source bytes retained");
   // A corrupt new object cannot replace a known original target. No transfers occur.
   Files.write(newTarget,new byte[]{1,2,3});String fallback=SideStoryTables.choose(leaf,oldTarget.toString());
   check(oldTarget.toString().equals(fallback),"bad206 cache returns known205 source without crash");
   check(Arrays.equals(before,Files.readAllBytes(oldTarget)),"failed refresh leaves prior205 cache intact");
   Files.write(newTarget,after);check(newTarget.toString().equals(SideStoryTables.choose(leaf,oldTarget.toString())),"subsequent valid206 cache refresh succeeds");
   changed++;
  }
  check(changed>0,"all changed event payloads exercised");check(Arrays.equals(saved,Files.readAllBytes(save)),"isolated saved progress retained");
  System.out.println("PASSED "+checks+" old205-target cache checks; changed="+changed);
 }
}
