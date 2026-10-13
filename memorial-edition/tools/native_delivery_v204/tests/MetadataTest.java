package O1;
import java.nio.file.*;
import java.util.*;
public class MetadataTest {
 static int checks;
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
 interface Task{void run()throws Exception;}
 static void reject(Task task,String why)throws Exception{try{task.run();throw new AssertionError(why);}catch(java.io.IOException ok){checks++;}}
 public static void main(String[] args)throws Exception{
  int expectedAPK=args.length>1?Integer.parseInt(args[1]):203;
  Path stage=Paths.get(args[0]);byte[] root=Files.readAllBytes(stage.resolve("payload/root_delivery.tsv")),content=Files.readAllBytes(stage.resolve("payload/content_delivery.tsv")),base=Files.readAllBytes(stage.resolve("payload/base_delivery.tsv")),release=Files.readAllBytes(stage.resolve("payload/delivery_release.tsv")),pointer=Files.readAllBytes(stage.resolve("asset_publication/manifest.json"));
  DeliveryPolicy.Config c=new DeliveryPolicy.Config(release,root,content);DeliveryPolicy.Revision r=new DeliveryPolicy.Revision(pointer,c,DeliveryPolicy.hash(base),base.length);
  r.verifyCatalogs(root,content,base);check(true,"all 5201 per-file JSON descriptors agree exactly with all three TSV catalogs");
  check(c.channel.equals("beta")&&c.apk==expectedAPK&&c.version==203,"correct bundled channel and APK pins");check(r.version==203&&r.minAPK==203,"real 2.96 MB pointer parses exact version fields");
  check(r.root.hash.equals(DeliveryPolicy.hash(root))&&r.content.hash.equals(DeliveryPolicy.hash(content)),"real catalogs exactly bound to bundled data");
  Map<String,ExtraContent.Entry> a=ExtraContent.parseCatalog(root),b=ExtraContent.parseCatalog(content);check(a.size()==663&&b.size()==1411,"real root and original content row counts");
  int overlap=0,boot=0;for(ExtraContent.Entry e:a.values()){check(DeliveryPolicy.payloadURL(e.url),"root release URL confined to existing repository");if(!e.path.startsWith("side_stories/"))boot++;if(b.containsKey(e.path)){ExtraContent.Entry f=b.get(e.path);check(e.hash.equals(f.hash)&&e.size==f.size,"overlapping root/original content identity agrees");overlap++;}}
  check(overlap==13&&boot==162,"all 13 stale overlap identities corrected; 162 boot dependencies");for(ExtraContent.Entry e:b.values())check(DeliveryPolicy.payloadURL(e.url),"original content trusted immutable repository source");
  Map<String,Object> parsed=DeliveryPolicy.map(DeliveryPolicy.Json.parse(pointer));check(((List<?>)parsed.get("assets")).size()==5201,"all 5201 per-asset metadata entries parsed");
  reject(()->new DeliveryPolicy.Config(new String(release,"UTF-8").replace("/beta/channels/beta/manifest.json","/main/channels/prod/manifest.json").getBytes("UTF-8"),root,content),"cross-channel pointer rejected");
  reject(()->new DeliveryPolicy.Revision(new String(pointer,"UTF-8").replace("\"channel\": \"beta\"","\"channel\": \"prod\"").getBytes("UTF-8"),c,DeliveryPolicy.hash(base),base.length),"cross-channel revision rejected");
  reject(()->new DeliveryPolicy.Revision(pointer,c,DeliveryPolicy.hash(new byte[]{0}),base.length),"base catalog replacement rejected");
  reject(()->new DeliveryPolicy.Revision(new String(pointer,"UTF-8").replace(DeliveryPolicy.PACKAGE,"com.invalid.package").getBytes("UTF-8"),c,DeliveryPolicy.hash(base),base.length),"wrong package rejected");
  reject(()->new DeliveryPolicy.Revision(new String(pointer,"UTF-8").replace(DeliveryPolicy.SIGNER,"0000000000000000000000000000000000000000000000000000000000000000").getBytes("UTF-8"),c,DeliveryPolicy.hash(base),base.length),"wrong signer identity rejected");
  reject(()->{DeliveryPolicy.Revision bad=new DeliveryPolicy.Revision(new String(pointer,"UTF-8").replaceFirst(a.values().iterator().next().hash,"0000000000000000000000000000000000000000000000000000000000000000").getBytes("UTF-8"),c,DeliveryPolicy.hash(base),base.length);bad.verifyCatalogs(root,content,base);},"JSON identity disagreement with catalog rejected");
  reject(()->{DeliveryPolicy.Revision bad=new DeliveryPolicy.Revision(new String(pointer,"UTF-8").replaceFirst(a.values().iterator().next().hash,"0000000000000000000000000000000000000000000000000000000000000000").getBytes("UTF-8"),c,DeliveryPolicy.hash(base),base.length);bad.validateNext(r);},"changed file hash without per-file revision bump rejected");
  reject(()->DeliveryPolicy.Json.parse("{\"x\":1,\"x\":2}".getBytes("UTF-8")),"duplicate JSON keys rejected");reject(()->DeliveryPolicy.Json.parse("{}x".getBytes("UTF-8")),"trailing JSON rejected");
  check(!GameAssets.safePath("cpk/../evil.dat")&&!GameAssets.safePath("font\\evil.ttf")&&!GameAssets.safePath("/cpk/root.cpk")&&GameAssets.safePath("side_stories/r2/JP/event.dat"),"nested paths admitted; traversal denied");
  check(!DeliveryPolicy.payloadURL("https://github.com/other/repo/releases/download/v1/x.bin")&&!DeliveryPolicy.payloadURL("https://github.com/"+DeliveryPolicy.REPO+"/releases/download/v1/x.bin#evil")&&!DeliveryPolicy.releaseURL("https://github.com/"+DeliveryPolicy.REPO+"/releases/latest/download/x.tsv"),"payload repository and immutable source confinement");
  Map<String,ExtraContent.Entry> empty=new LinkedHashMap<>();reject(()->GameAssets.validateGraph(empty,a),"dropping preserved asset paths rejected");
  Map<String,ExtraContent.Entry> staticChanged=new LinkedHashMap<>(b);ExtraContent.Entry staticEntry=b.values().iterator().next();ExtraContent.Entry replacement=new ExtraContent.Entry(new String[]{staticEntry.path,"0000000000000000000000000000000000000000000000000000000000000000",Long.toString(staticEntry.size),staticEntry.url,Long.toString(staticEntry.offset),Long.toString(staticEntry.wireSize),Integer.toString(staticEntry.method),Long.toString(staticEntry.sourceSize)});staticChanged.put(replacement.path,replacement);reject(()->GameAssets.validateGraph(staticChanged,b),"hardcoded static chooser replacement requires APK engine update");
  System.out.println("PASSED "+checks+" real-metadata admission checks; root=663 content=1411 overlap=13 union=2061 base=3127 metadata=5201 boot=162 game-root=501");
 }
}
