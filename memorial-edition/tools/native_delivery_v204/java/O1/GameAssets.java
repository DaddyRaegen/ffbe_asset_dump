package O1;
import android.content.Context;
import android.content.res.AssetManager;
import android.content.res.AssetFileDescriptor;
import android.graphics.Typeface;
import android.os.ParcelFileDescriptor;
import android.util.AtomicFile;
import java.io.*;
import java.net.*;
import java.util.*;

/** Individually verified game data; existing ContentDownloader owns every network transfer. */
public final class GameAssets {
 private static DeliveryPolicy.Config config;
 private static byte[] bundledRoot,bundledContent,bundledBase;
 private static String activeRootHash;
 private static Map<String,ExtraContent.Entry> roots;
 private static Set<String> bootPaths;
 private static DeliveryPolicy.Revision pending;
 private static DeliveryPolicy.Revision activeRevision;
 private static Map<String,ExtraContent.Entry> pendingCatalog;
 private static long highest;
 interface Linker {boolean same(File target,File source)throws Exception;void create(File target,File source)throws Exception;}
 static Linker linker=new Linker(){public boolean same(File target,File source)throws Exception{return target.getCanonicalFile().equals(source.getCanonicalFile());}public void create(File target,File source)throws Exception{Class.forName("android.system.Os").getMethod("symlink",String.class,String.class).invoke(null,source.getAbsolutePath(),target.getAbsolutePath());}};
 private static boolean checked;
 private static volatile boolean bootReady;
 private static boolean runtimeLoaded;
 public static String status="APK-pinned baseline";
 public static boolean safePath(String p){
  if(p==null||p.length()>512||p.indexOf('\\')>=0||!p.matches("(side_stories|story_ports|battle|encyclopedia|android|bin|bishamon|cpk|font|html|memory_room|plate_pack|shader)/[A-Za-z0-9_./-]+"))return false;
  for(String part:p.split("/",-1))if(part.isEmpty()||part.equals(".")||part.equals(".."))return false;return true;
 }
 static byte[] read(InputStream in,int limit)throws Exception {try(InputStream s=in;ByteArrayOutputStream b=new ByteArrayOutputStream()){byte[] q=new byte[65536];int n;while((n=s.read(q))!=-1){if(b.size()>limit-n)throw new IOException("Metadata bounds exceeded");b.write(q,0,n);}return b.toByteArray();}}
 static File home()throws Exception {return new File(ExtraContent.files(),"game_assets/releases/"+DeliveryPolicy.ENGINE+"/"+config.channel);}
 private static File disk(String name)throws Exception {return new File(home(),name);}
 private static Map<String,ExtraContent.Entry> union(Map<String,ExtraContent.Entry> a,Map<String,ExtraContent.Entry> b)throws Exception {
  Map<String,ExtraContent.Entry> m=new LinkedHashMap<>(a);for(ExtraContent.Entry e:b.values()){ExtraContent.Entry previous=m.get(e.path);if(previous!=null&&!same(previous,e))throw new IOException("Conflicting game data identity: "+e.path);m.put(e.path,e);}return m;
 }
 private static boolean same(ExtraContent.Entry a,ExtraContent.Entry b){return a.hash.equals(b.hash)&&a.size==b.size;}
 static synchronized Map<String,ExtraContent.Entry> initialize(byte[] content,Map<String,ExtraContent.Entry> extras)throws Exception {
  bundledContent=content;bundledRoot=read(ExtraContent.bundled("root_delivery.tsv"),DeliveryPolicy.MAX_CATALOG);bundledBase=read(ExtraContent.bundled("base_delivery.tsv"),DeliveryPolicy.MAX_CATALOG);
  config=new DeliveryPolicy.Config(read(ExtraContent.bundled("delivery_release.tsv"),4096),bundledRoot,bundledContent);
  activeRevision=revision(read(ExtraContent.bundled("game_asset_manifest.json"),DeliveryPolicy.MAX_POINTER));activeRevision.verifyCatalogs(bundledRoot,bundledContent,bundledBase);if(activeRevision.version!=config.version||activeRevision.minAPK>config.apk)throw new IOException("Signed asset baseline version disagrees");
  roots=ExtraContent.parseCatalog(bundledRoot);Map<String,ExtraContent.Entry> baseline=union(extras,roots);activeRootHash=config.rootHash;highest=config.version;
  BundledAssets.initialize(config,activeRevision,roots);
  try {
   String[] state=new String(read(new AtomicFile(disk("state.tsv")).openRead(),4096),"UTF-8").split("\n",-1);
   if(state.length!=3||!state[0].equals("ffbe-game-assets-state-v1")||!state[2].isEmpty())throw new IOException("Invalid asset state");String[] fields=state[1].split("\t",-1);if(fields.length!=3)throw new IOException("Invalid state fields");
   highest=Math.max(config.version,Long.parseLong(fields[0]));
   // A complete queued revision becomes active only before native startup on this launch.
   String[] ids={fields[2],fields[1]};for(String id:ids)if(id.matches("[a-f0-9]{64}")){
    try {DeliveryPolicy.Revision r=revision(read(new FileInputStream(disk(id+".json")),DeliveryPolicy.MAX_POINTER));if(!r.id.equals(id))throw new IOException("Selected descriptor checksum mismatch");if(r.version<config.version)continue;if(r.minAPK>config.apk)throw new IOException("Selected asset graph requires a newer APK");
     byte[] rb=catalogOrRepair(r.root),cb=catalogOrRepair(r.content);r.verifyCatalogs(rb,cb,bundledBase);r.validateNext(activeRevision);
     if(id.equals(fields[2])&&fields[1].matches("[a-f0-9]{64}")){DeliveryPolicy.Revision previous=revision(read(new FileInputStream(disk(fields[1]+".json")),DeliveryPolicy.MAX_POINTER));r.validateNext(previous);}
     Map<String,ExtraContent.Entry> nr=ExtraContent.parseCatalog(rb),nc=ExtraContent.parseCatalog(cb),graph=union(nc,nr);validateGraph(graph,baseline);
     // Preserve the selected graph even if a cache object was lost: repair missing files,
     // rather than silently selecting an older roster or event manifest.
     roots=nr;activeRootHash=r.root.hash;activeRevision=r;saveState(highest,id,"baseline");baseline=graph;status="cached asset version "+r.version+"; missing files will be repaired";break;
    }catch(Exception invalid){if(id.equals(fields[1]))throw new IOException("Active asset metadata is damaged; repair is required",invalid);}
   }
  }catch(FileNotFoundException noState){highest=config.version;}
  bootPaths=new LinkedHashSet<>();for(String p:roots.keySet())if(!p.startsWith("side_stories/"))bootPaths.add(p);
  return baseline;
 }
 static boolean bootPath(String name){return bootPaths!=null&&bootPaths.contains(name);}
 static DeliveryPolicy.Revision revision(byte[] bytes)throws Exception {return new DeliveryPolicy.Revision(bytes,config,DeliveryPolicy.hash(bundledBase),bundledBase.length);}
 static byte[] catalog(DeliveryPolicy.Catalog c)throws Exception {byte[] b=read(new FileInputStream(disk(c.hash+".tsv")),DeliveryPolicy.MAX_CATALOG);if(b.length!=c.bytes||!DeliveryPolicy.hash(b).equals(c.hash))throw new IOException("Catalog checksum mismatch");return b;}
 static byte[] catalogOrRepair(DeliveryPolicy.Catalog c)throws Exception {try{return catalog(c);}catch(IOException damaged){File p=disk(c.hash+".tsv");if(p.isFile()){File quarantine=disk(c.hash+".corrupt-"+System.nanoTime());if(!p.renameTo(quarantine))throw new IOException("Cannot isolate damaged catalog",damaged);}return fetchCatalog(c);}}
 static void immutable(File p,byte[] bytes)throws Exception {if(p.isFile()){if(!Arrays.equals(read(new FileInputStream(p),DeliveryPolicy.MAX_CATALOG),bytes))throw new IOException("Immutable metadata collision");return;}File parent=p.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs()&&!parent.isDirectory())throw new IOException("Metadata directory unavailable");File t=new File(p+".tmp");try(FileOutputStream out=new FileOutputStream(t)){out.write(bytes);out.getFD().sync();}if(!t.renameTo(p))throw new IOException("Cannot retain verified metadata");}
 static void saveState(long n,String active,String next)throws Exception {File p=disk("state.tsv");if(!p.getParentFile().isDirectory()&&!p.getParentFile().mkdirs()&&!p.getParentFile().isDirectory())throw new IOException("State directory unavailable");AtomicFile file=new AtomicFile(p);FileOutputStream out=null;try{out=file.startWrite();out.write(("ffbe-game-assets-state-v1\n"+n+"\t"+active+"\t"+next+"\n").getBytes("UTF-8"));file.finishWrite(out);out=null;}finally{if(out!=null)file.failWrite(out);}}
 private static String activeID()throws Exception {try{String[] ll=new String(read(new AtomicFile(disk("state.tsv")).openRead(),4096),"UTF-8").split("\n",-1);return ll[1].split("\t",-1)[1];}catch(Exception e){return "baseline";}}
 private static byte[] fetchPointer()throws Exception {
  HttpURLConnection c=(HttpURLConnection)new URL(config.pointer).openConnection();try{c.setConnectTimeout(15000);c.setReadTimeout(20000);c.setInstanceFollowRedirects(false);c.setUseCaches(false);c.setRequestProperty("Accept-Encoding","identity");if(c.getResponseCode()!=200)throw new IOException("Asset manifest unavailable");return read(c.getInputStream(),DeliveryPolicy.MAX_POINTER);}finally{c.disconnect();}
 }
 private static byte[] fetchCatalog(DeliveryPolicy.Catalog c)throws Exception {File part=disk(c.hash+".part");ResumableTransfer.fetch(c.url,part,0,c.bytes,c.bytes,new ResumableTransfer.Progress(){public void received(long n){}});byte[] b=read(new FileInputStream(part),DeliveryPolicy.MAX_CATALOG);if(b.length!=c.bytes||!DeliveryPolicy.hash(b).equals(c.hash)){part.delete();throw new IOException("Catalog checksum failed");}immutable(disk(c.hash+".tsv"),b);part.delete();return b;}
 static void validateGraph(Map<String,ExtraContent.Entry> next,Map<String,ExtraContent.Entry> old)throws Exception {
  BundledAssets.validateGraph(next);
  if(!next.keySet().containsAll(old.keySet()))throw new IOException("Asset revision removes preserved paths");
  for(ExtraContent.Entry e:next.values()){
   ExtraContent.Entry previous=old.get(e.path);if(previous!=null&&same(previous,e))continue;
   if(e.path.matches("(story_ports|battle|encyclopedia)/.*")&&!e.path.equals("story_ports/SLB_LDA.usm"))throw new IOException("Static override changes require a compatible APK chooser release");
   if(!safePath(e.path)||!e.path.matches(".*\\.(dat|cpk|acf|acb|awb|usm|txt|tsv|json|png|jpg|jpeg|html|css|otf|ttf|bin|vsh|fsh)"))throw new IOException("Asset revision changes executable or unsupported data");
   if(e.path.startsWith("bin/"))throw new IOException("Vendor executable replacement requires an APK release");
   if(!DeliveryPolicy.payloadURL(e.url))throw new IOException("Asset revision source is not an immutable release in the configured repository");
  }
 }
 static synchronized Map<String,ExtraContent.Entry> checkUpdate(Map<String,ExtraContent.Entry> active){
  if(checked)return null;checked=true;
  try{DeliveryPolicy.Revision r=revision(fetchPointer());if(r.version<=highest){status="current asset manifest";return null;}if(r.minAPK>config.apk){status="asset revision requires a newer APK";return null;}
   byte[] rb=fetchCatalog(r.root),cb=fetchCatalog(r.content);r.verifyCatalogs(rb,cb,bundledBase);r.validateNext(activeRevision);Map<String,ExtraContent.Entry> nr=ExtraContent.parseCatalog(rb),nc=ExtraContent.parseCatalog(cb),next=union(nc,nr);validateGraph(next,active);immutable(disk(r.id+".json"),r.descriptor);pending=r;pendingCatalog=next;status="asset version "+r.version+" staged for verified incremental download";return next;
  }catch(Exception offline){status="asset manifest unavailable; verified current data retained";return null;}
 }
 static synchronized boolean stageNextLaunch(Map<String,ExtraContent.Entry> catalog)throws Exception {if(pending==null||catalog!=pendingCatalog||!ExtraContent.ready(catalog))return false;highest=Math.max(highest,pending.version);saveState(highest,activeID(),pending.id);status="asset version "+pending.version+" verified; applies on next launch";pending=null;pendingCatalog=null;return true;}
 static synchronized void discardPending(){pending=null;pendingCatalog=null;}
 public static boolean bootReady(){return bootReady;}
 static DeliveryPolicy.Config configuration(){return config;}
 public static File tree()throws Exception {return new File(ExtraContent.files(),"game_assets/"+activeRootHash+"/tree");}
 private static void link(File target,File source,boolean repairBundled)throws Exception {
  File parent=target.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs()&&!parent.isDirectory())throw new IOException("Asset view unavailable");
  if(target.exists()){if(linker.same(target,source))return;if(!repairBundled||!target.isFile()||!target.delete())throw new IOException("Asset view collision");}
  else if(repairBundled)target.delete(); // Remove a dangling owned bootstrap link.
  // API21 public filesystem bridge; does not mutate Android AssetManager or load data as an APK.
  linker.create(target,source);
 }
 private static void prepare(Set<String> paths)throws Exception {Map<String,ExtraContent.Entry> graph=ExtraContent.current();for(String path:paths){ExtraContent.Entry e=graph.get(path);if(e==null)throw new IOException("Missing root asset");File source=ExtraContent.available(e,graph);if(source==null)throw new IOException("Unverified root asset: "+path);link(new File(tree(),path),source,BundledAssets.contains(e));}}
 public static synchronized void prepareBoot()throws Exception {prepare(bootPaths);File marker=new File(ExtraContent.files(),"game_assets/active-root.txt");if(!marker.getParentFile().isDirectory()&&!marker.getParentFile().mkdirs()&&!marker.getParentFile().isDirectory())throw new IOException("Asset marker directory unavailable");AtomicFile atomic=new AtomicFile(marker);FileOutputStream out=null;try{out=atomic.startWrite();out.write((tree().getAbsolutePath()+"/\n").getBytes("UTF-8"));atomic.finishWrite(out);out=null;}finally{if(out!=null)atomic.failWrite(out);}bootReady=true;}
 public static synchronized void prepareCurrentTree()throws Exception {prepare(roots.keySet());}
 static File rootFile(String name)throws Exception {if(name.startsWith("assets/"))name=name.substring(7);if(!safePath(name)||roots==null||!roots.containsKey(name))return null;ExtraContent.Entry e=ExtraContent.current().get(name);File f=ExtraContent.available(e,ExtraContent.current());if(f==null)throw new FileNotFoundException("Download required: "+name);return f;}
 public static InputStream open(AssetManager assets,String name)throws IOException {try{File f=rootFile(name);return f==null?assets.open(name):new FileInputStream(f);}catch(IOException e){throw e;}catch(Exception e){throw new IOException("External asset unavailable",e);}}
 public static InputStream open(AssetManager assets,String name,int mode)throws IOException {return open(assets,name);}
 public static AssetFileDescriptor openFd(AssetManager assets,String name)throws IOException {try{File f=rootFile(name);return f==null?assets.openFd(name):new AssetFileDescriptor(ParcelFileDescriptor.open(f,ParcelFileDescriptor.MODE_READ_ONLY),0,f.length());}catch(IOException e){throw e;}catch(Exception e){throw new IOException("External media unavailable",e);}}
 public static Typeface typeface(AssetManager assets,String name){try{File f=rootFile(name);return f==null?Typeface.createFromAsset(assets,name):Typeface.createFromFile(f);}catch(Exception e){throw new IllegalStateException("External font unavailable",e);}}
 public static String[] list(AssetManager assets,String dir)throws IOException {try{Set<String> names=new TreeSet<>();String prefix=dir.isEmpty()?"":dir+"/";if(roots!=null)for(String p:roots.keySet())if(p.startsWith(prefix)){String suffix=p.substring(prefix.length());names.add(suffix.split("/",2)[0]);}for(String p:assets.list(dir))names.add(p);return names.toArray(new String[0]);}catch(IOException e){throw e;}catch(Exception e){throw new IOException("Asset directory unavailable",e);}}
 public static String webURL(String value){if(value==null||!value.startsWith("file:///android_asset/"))return value;try{String path=value.substring(22),fragment="";int q=path.indexOf('#'),query=path.indexOf('?');if(query>=0&&(q<0||query<q))q=query;if(q>=0){fragment=path.substring(q);path=path.substring(0,q);}File f=rootFile(path);if(f==null&&roots!=null){String dir=path.endsWith("/")?path.substring(0,path.length()-1):path;if(dir.matches("[A-Za-z0-9_./-]*")&&!Arrays.asList(dir.split("/",-1)).contains("..")&&!Arrays.asList(dir.split("/",-1)).contains(".")){for(String name:roots.keySet())if(name.startsWith(dir.isEmpty()?"":dir+"/")){f=new File(tree(),dir);break;}}}return f==null?value:f.toURI().toString()+fragment;}catch(Exception e){throw new IllegalStateException("External page unavailable",e);}}
 public static synchronized void runtime(Context context){if(runtimeLoaded)return;try{File script=new File(context.getFilesDir(),"frida_script.js");try(InputStream in=context.getAssets().open("frida_script.js");FileOutputStream out=new FileOutputStream(script)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);out.getFD().sync();}System.loadLibrary("frida-gadget");runtimeLoaded=true;}catch(Exception e){throw new IllegalStateException("Cannot initialize signed runtime",e);}}
}
