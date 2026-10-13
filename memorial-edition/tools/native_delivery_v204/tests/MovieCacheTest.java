package O1;
import android.app.*;
import java.io.*;
import java.nio.file.*;
import java.nio.file.attribute.FileTime;
import java.util.*;
import android.util.AtomicFile;
public class MovieCacheTest {
 static int checks;static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
 public static void main(String[] args)throws Exception {
  for(boolean modern:new boolean[]{false,true}){AtomicFile.MODE_NEW_FILE=modern;
  Path root=Files.createTempDirectory(Paths.get(args[0]),"movie-cache-"),files=Files.createDirectories(root.resolve("files")),assets=Files.createDirectories(root.resolve("assets"));ActivityThread.app=new Application(files.toFile(),assets.toFile());
  byte[] first={1,2,3,4},second={5,6,7,8};String old=DeliveryPolicy.hash(first),newer=DeliveryPolicy.hash(second);Path source=root.resolve("source.usm");Files.write(source,first);
  check(MovieAssets.prepare("fixture.usm",source.toFile(),old,""),"new selected movie prepared");Path movie=files.resolve("fixture.usm");check(Arrays.equals(Files.readAllBytes(movie),first),"derived native filename contains verified bytes");
  Files.setLastModifiedTime(movie,FileTime.fromMillis(100000));long time=Files.getLastModifiedTime(movie).toMillis();MovieAssets.prepare("fixture.usm",source.toFile(),old,"");check(Files.getLastModifiedTime(movie).toMillis()==time,"complete derived movie reused without recopy");
  Files.write(movie,new byte[]{1,2,3,9});check(MovieAssets.prepare("fixture.usm",source.toFile(),old,"")&&Arrays.equals(Files.readAllBytes(movie),first),"same-length corrupt owned movie repaired");
  Files.write(source,second);check(MovieAssets.prepare("fixture.usm",source.toFile(),newer,"")&&Arrays.equals(Files.readAllBytes(movie),second),"higher selected movie replaces known owned prior copy");
  Path unfamiliar=files.resolve("unfamiliar.usm");Files.write(unfamiliar,first);check(!MovieAssets.prepare("unfamiliar.usm",source.toFile(),newer,"")&&Arrays.equals(Files.readAllBytes(unfamiliar),first),"unrecognized unowned prior movie preserved");
  check(MovieAssets.prepare("unfamiliar.usm",source.toFile(),newer,old)&&Arrays.equals(Files.readAllBytes(unfamiliar),second),"explicit accepted source chain allows controlled update");
  boolean rejected=false;try{MovieAssets.prepare("fixture.usm",source.toFile(),old,"");}catch(IOException wrong){rejected=true;}check(rejected&&Arrays.equals(Files.readAllBytes(movie),second),"unverified movie source rejected without changing installed copy");
  check(Files.isRegularFile(files.resolve("game_assets/derived_movies/fixture.usm.tsv")),"derived ownership persists across cold startup");
  AtomicFile rollback=new AtomicFile(movie.toFile());FileOutputStream out=rollback.startWrite();out.write(new byte[]{9,9,9,9});rollback.failWrite(out);check(Arrays.equals(Files.readAllBytes(movie),second),"failed atomic write retains previous complete movie in both styles");Path aborted=files.resolve("aborted.usm");AtomicFile incomplete=new AtomicFile(aborted.toFile());out=incomplete.startWrite();out.write(first);incomplete.failWrite(out);check(!Files.exists(aborted)&&!Files.exists(Paths.get(aborted+".new")),"failed first write never publishes incomplete movie");
  }
  System.out.println("PASSED "+checks+" derived movie checksum/ownership checks across base/backup and modern .new atomic writes");
 }
}
