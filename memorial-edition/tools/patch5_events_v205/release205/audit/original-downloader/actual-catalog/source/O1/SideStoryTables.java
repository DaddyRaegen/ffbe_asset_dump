package O1;
import java.io.*;
import java.lang.reflect.Method;
import java.security.MessageDigest;
import java.util.*;

/** Exact-version, lazy asset overrides for the Side Story test catalog. */
public final class SideStoryTables {
 private static Map<String,String[]> entries;
 private static Object app() throws Exception {return Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null);}
 private static File files(Object a)throws Exception{return (File)Class.forName("android.content.Context").getMethod("getFilesDir").invoke(a);}
 private static InputStream asset(Object a,String name)throws Exception {
  Object manager=Class.forName("android.content.Context").getMethod("getAssets").invoke(a);
  return ExtraContent.open("side_stories/"+name);
 }
 private static void load(Object a)throws Exception {
  if(entries!=null)return;Map<String,String[]> next=new LinkedHashMap<>();
  try(BufferedReader r=new BufferedReader(new InputStreamReader(asset(a,"manifest.tsv"),"UTF-8"))){String line;while((line=r.readLine())!=null){String[] p=line.split("\t",-1);if((p.length!=3&&p.length!=4)||!p[0].matches("(?:[A-Za-z0-9_.-]+|r2_scene_(jp|gl)/[a-f0-9]{16}/[A-Za-z0-9_.-]+[.]cpk)")||!p[1].matches("[a-f0-9]{64}"))throw new IOException("Invalid manifest");next.put(p[0],new String[]{p[1],p[2],p.length==4?p[3]:""});}}
  entries=next;
 }
 public static synchronized String choose(String name,String original) {
  if(name==null||!name.matches("(?:[A-Za-z0-9_.-]+|r2_scene_(jp|gl)/[a-f0-9]{16}/[A-Za-z0-9_.-]+[.]cpk)"))return original;
  try {
   Object a=app();if(a==null)return original;load(a);String[] entry=entries.get(name);if(entry==null)return original;
   String expected=entry[0],assetName=name;
   // An unknown pre-existing source remains authoritative.
   if(original!=null&&!original.isEmpty()&&new File(original).isFile()){
    String actual=hash(new FileInputStream(original));
    if(!actual.equals(expected)&&!Arrays.asList(entry[1].split(",")).contains(actual))return original;
    for(String variant:entry[2].split(",")){
     String[] pair=variant.split("=",-1);if(pair.length!=2||!pair[0].equals(actual))continue;
     String[] alternate=entries.get(pair[1]);if(alternate==null)return original;
     assetName=pair[1];expected=alternate[0];break;
    }
   } else if(!entry[1].isEmpty()&&name.endsWith(".dat"))return original;
   File dir=new File(files(a),"side_stories/"+expected);File target=new File(dir,name);
   if(target.isFile()&&expected.equals(hash(new FileInputStream(target))))return target.getAbsolutePath();
   File parent=target.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs())return original;File temp=new File(dir,name+".tmp");
   try(InputStream in=asset(a,assetName);FileOutputStream out=new FileOutputStream(temp)) {byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);out.getFD().sync();}
   if(!expected.equals(hash(new FileInputStream(temp)))){temp.delete();return original;}
   if(target.exists()&&!target.delete())return original;if(!temp.renameTo(target))return original;
   return target.getAbsolutePath();
  }catch(Exception e){return original;}catch(LinkageError e){return original;}
 }
 public static synchronized void prepareIndexes(){
  try {Object a=app();if(a==null)return;load(a);File root=files(a);
   for(Map.Entry<String,String[]> e:entries.entrySet()){
    String name=e.getKey();
    if(name.endsWith(".usm")){
     File movie=new File(root,name);if(movie.exists())continue;String source=choose(name,null);if(source==null)continue;
     File temporary=new File(root,"side-story-"+name+".tmp");
     try(InputStream in=new FileInputStream(source);FileOutputStream out=new FileOutputStream(temporary)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);out.getFD().sync();}
     if(e.getValue()[0].equals(hash(new FileInputStream(temporary)))&&!movie.exists())temporary.renameTo(movie);
     continue;
    }
    if(!name.endsWith(".dat")||name.endsWith("-legacy.dat"))continue;
    String revision=Arrays.toString(e.getValue());
    for(String variant:e.getValue()[2].split(",")){String[] pair=variant.split("=",-1);if(pair.length==2&&entries.containsKey(pair[1]))revision+=entries.get(pair[1])[0];}
    String version=hash(new ByteArrayInputStream(revision.getBytes("UTF-8")));
    File marker=new File(root,"side_stories/index-v2-"+version+".ready");if(marker.isFile())continue;
    if(!marker.getParentFile().isDirectory()&&!marker.getParentFile().mkdirs())continue;
    File index=new File(root,name.substring(0,name.length()-4)+".i");File backup=new File(root,"side_stories/index-v2-"+version+".backup");
    if(index.exists()&&!index.renameTo(backup))continue;marker.createNewFile();
   }
  }catch(Exception e){}
 }
 private static String hash(InputStream in)throws Exception {MessageDigest d=MessageDigest.getInstance("SHA-256");try{byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}finally{in.close();}StringBuilder s=new StringBuilder();for(byte b:d.digest())s.append(String.format("%02x",b&255));return s.toString();}
}
