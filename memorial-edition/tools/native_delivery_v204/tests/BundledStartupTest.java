package O1;

import android.app.*;
import android.util.AtomicFile;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

/** Isolated APK assets/cache and fake HTTPS; never opens Android runtime files. */
public class BundledStartupTest extends NativeDeliveryTest {
 static byte[] rootBytes,contentBytes,baseBytes,manifestBytes;
 static String inventoryText;
 static Path fixtureParent;
 interface Action {void run()throws Exception;}

 static void fixture(long apk,boolean inventory)throws Exception {
  reset();requests=0;offline=false;routes.clear();requested.clear();
  Path fixture=Files.createTempDirectory(fixtureParent,"bundled-startup-");
  assets=Files.createDirectories(fixture.resolve("assets"));files=Files.createDirectories(fixture.resolve("files"));
  ActivityThread.app=new Application(files.toFile(),assets.toFile());
  rootBytes=catalog(row("cpk/root.cpk","boot-pack")+row("font/root.ttf","boot-font")+row("side_stories/event.dat","roster-old"));
  contentBytes=catalog(row("side_stories/remote.dat","remote-event"));baseBytes=bytes("ffbe-base-v1\n");
  manifestBytes=descriptor(203,rootBytes,contentBytes,baseBytes);
  Files.write(assets.resolve("root_delivery.tsv"),rootBytes);Files.write(assets.resolve("content_delivery.tsv"),contentBytes);
  Files.write(assets.resolve("base_delivery.tsv"),baseBytes);Files.write(assets.resolve("game_asset_manifest.json"),manifestBytes);
  Files.write(assets.resolve("delivery_release.tsv"),bytes("ffbe-delivery-release-v1\nbeta\t203\t"+apk+"\t"+DeliveryPolicy.hash(rootBytes)+"\t"+DeliveryPolicy.hash(contentBytes)+"\t"+DeliveryPolicy.metadataURL("beta","patch_version.json")+"\t"+DeliveryPolicy.metadataURL("beta","manifest.json")+"\n"));
  Files.createDirectories(assets.resolve("cpk"));Files.createDirectories(assets.resolve("font"));
  Files.write(assets.resolve("cpk/root.cpk"),bytes("boot-pack"));Files.write(assets.resolve("font/root.ttf"),bytes("boot-font"));
  StringBuilder rows=new StringBuilder();
  for(ExtraContent.Entry entry:ExtraContent.parseCatalog(rootBytes).values())if(!entry.path.startsWith("side_stories/")){
   if(rows.length()>0)rows.append(',');rows.append("{\"namespace\":\"root\",\"path\":\"").append(entry.path).append("\",\"apk_path\":\"assets/").append(entry.path).append("\",\"bytes\":").append(entry.size).append(",\"sha256\":\"").append(entry.hash).append("\"}");
  }
  inventoryText="{\"schema\":\"ffbe-bootstrap-inventory-v1\",\"package\":\""+DeliveryPolicy.PACKAGE+"\",\"signing_certificate_sha256\":\""+DeliveryPolicy.SIGNER+"\",\"APK_version\":"+apk+",\"asset_version\":203,\"manifest_sha256\":\""+DeliveryPolicy.hash(manifestBytes)+"\",\"assets\":["+rows+"]}";
  if(inventory)Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText));
 }

 static void rejects(Action action,String why)throws Exception {
  boolean rejected=false;try{action.run();}catch(IOException expected){rejected=true;}
  check(rejected&&!GameAssets.bootReady()&&requests==0,why+" fails closed before native startup or network");
 }

 static void behavior(boolean modern)throws Exception {
  AtomicFile.MODE_NEW_FILE=modern;fixture(204,true);
  Path save=files.resolve("fixture-save.bin");Files.write(save,bytes("existing-save"));
  ExtraContent.Entry core=ExtraContent.parseCatalog(rootBytes).get("cpk/root.cpk");
  Path partial=Files.createDirectories(files.resolve("content_delivery")).resolve(core.hash+".part");Files.write(partial,bytes("retained-partial"));
  ExtraContent.load();check(requests==0&&ExtraContent.missingBoot().isEmpty(),"first launch admits every signed APK boot file without HTTPS");
  ContentDownloader.downloadBootAssets(null);check(GameAssets.bootReady()&&requests==0,"boot filesystem prepares without a startup download");
  check(ExtraContent.missing().size()==2,"bundled core absent from native missing queue; nonbootstrap remains incremental");
  try(InputStream in=GameAssets.open(ActivityThread.app.getAssets(),"cpk/root.cpk")){check(Arrays.equals(GameAssets.read(in,1024),bytes("boot-pack")),"Java helper uses verified seeded bytes");}
  try(InputStream in=ActivityThread.app.getAssets().open("cpk/root.cpk")){check(Arrays.equals(GameAssets.read(in,1024),bytes("boot-pack")),"raw APK AssetManager startup path retains original bytes");}
  check(Arrays.equals(Files.readAllBytes(save),bytes("existing-save"))&&Arrays.equals(Files.readAllBytes(partial),bytes("retained-partial")),"seeding preserves saves and remote partials");
  core=ExtraContent.current().get("cpk/root.cpk");Path cached=ExtraContent.target(core).toPath();byte[] corrupt=Files.readAllBytes(cached);corrupt[0]^=1;Files.write(cached,corrupt);
  File repaired=ExtraContent.available(core,ExtraContent.current());check(repaired!=null&&ExtraContent.hash(repaired).equals(core.hash)&&requests==0,"same-size startup cache corruption repaired from APK without HTTPS");
  check(Arrays.equals(Files.readAllBytes(save),bytes("existing-save"))&&Arrays.equals(Files.readAllBytes(partial),bytes("retained-partial")),"repair preserves saves and remote partials");
  int before=requests;downloadAll();check(requests==before+2&&ExtraContent.missing().isEmpty(),"only two absent nonbootstrap hashes fetched from immutable Github routes");
  for(String url:requested)check(!url.contains(DeliveryPolicy.hash(bytes("boot-pack")))&&!url.contains(DeliveryPolicy.hash(bytes("boot-font"))),"no bundled core network requests");
  GameAssets.prepareCurrentTree();check(requests==2,"native graph links all ready assets without extra transfers");
  // A compatible data graph must not replace raw APK startup bytes behind native handles.
  byte[] changedRoot=catalog(row("cpk/root.cpk","changed!!")+row("font/root.ttf","boot-font")+row("side_stories/event.dat","roster-old"));
  boolean denied=false;try{GameAssets.validateGraph(ExtraContent.parseCatalog(changedRoot),ExtraContent.current());}catch(IOException expected){denied=expected.getMessage().contains("newer APK");}
  check(denied,"changed bundled core rejected with explicit APK requirement");
  routes.put(DeliveryPolicy.metadataURL("beta","manifest.json"),descriptor(204,changedRoot,contentBytes,baseBytes));ExtraContent.checkHostedUpdate();
  check(ExtraContent.current().get("cpk/root.cpk").hash.equals(core.hash)&&ExtraContent.missing().isEmpty(),"hosted incompatible core revision leaves current verified graph authoritative");
  ExtraContent.Entry changed=ExtraContent.parseCatalog(changedRoot).get("cpk/root.cpk");check(!BundledAssets.contains(changed),"stale APK bytes never qualify a changed asset hash");
 }

 public static void main(String[] args)throws Exception {
  fixtureParent=Paths.get(args[0]);Files.createDirectories(fixtureParent);
  URL.setURLStreamHandlerFactory(p->p.equals("https")?new URLStreamHandler(){protected URLConnection openConnection(URL u){return new Conn(u);}}:null);
  ResumableTransfer.delay=ms->{};GameAssets.linker=new GameAssets.Linker(){public boolean same(File target,File source)throws Exception{return Files.isSameFile(target.toPath(),source.toPath());}public void create(File target,File source)throws Exception{Files.createLink(target.toPath(),source.toPath());}};
  behavior(false);behavior(true);
  fixture(204,false);rejects(()->ExtraContent.load(),"required inventory absence");
  fixture(203,false);ExtraContent.load();check(ExtraContent.missingBoot().size()==2&&requests==0,"legacy203 fixture absence retains strict external boot behavior");
  fixture(204,true);Files.write(assets.resolve("bootstrap_inventory.json"),bytes("{invalid}"));rejects(()->ExtraContent.load(),"malformed inventory");
  fixture(204,true);Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText.replace(DeliveryPolicy.PACKAGE,"com.example.wrong")));rejects(()->ExtraContent.load(),"wrong inventory package");
  fixture(204,true);Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText.replace(DeliveryPolicy.SIGNER,String.join("",Collections.nCopies(64,"0")))));rejects(()->ExtraContent.load(),"wrong inventory signer");
  fixture(204,true);Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText.replace("\"APK_version\":204","\"APK_version\":205")));rejects(()->ExtraContent.load(),"wrong inventory APK version");
  fixture(204,true);Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText.replace(DeliveryPolicy.hash(manifestBytes),String.join("",Collections.nCopies(64,"0")))));rejects(()->ExtraContent.load(),"wrong signed manifest pin");
  fixture(204,true);Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText.replace(DeliveryPolicy.hash(bytes("boot-pack")),DeliveryPolicy.hash(bytes("wrongpack")))));rejects(()->ExtraContent.load(),"wrong inventory member hash");
  fixture(204,true);Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText.replace("assets/cpk/root.cpk","assets/../cpk/root.cpk")));rejects(()->ExtraContent.load(),"unsafe APK inventory path");
  fixture(204,true);int first=inventoryText.indexOf("{\"namespace\":\"root\"");int firstEnd=inventoryText.indexOf('}',first)+1;Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText.substring(0,firstEnd)+","+inventoryText.substring(first,firstEnd)+inventoryText.substring(firstEnd)));rejects(()->ExtraContent.load(),"duplicate startup identity");
  fixture(204,true);int start=inventoryText.indexOf("{\"namespace\":\"root\",\"path\":\"font/");Files.write(assets.resolve("bootstrap_inventory.json"),bytes(inventoryText.substring(0,start-1)+"]}"));rejects(()->ExtraContent.load(),"incomplete boot inventory");
  fixture(204,true);Files.delete(assets.resolve("font/root.ttf"));rejects(()->ExtraContent.load(),"missing declared APK asset");
  fixture(204,true);Files.write(assets.resolve("cpk/root.cpk"),bytes("corrupted"));rejects(()->ExtraContent.load(),"same-size declared APK asset checksum mismatch");
  System.out.println("PASSED "+checks+" bundled-startup host checks (no Android native runtime or device files)");
 }
}
