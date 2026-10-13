package O1;

import java.io.*;
import java.util.*;

/** Signed APK startup bytes are a verified source for the existing per-file cache. */
public final class BundledAssets {
 private static volatile Map<String,ExtraContent.Entry> pinned=Collections.emptyMap();
 private BundledAssets(){}

 static void initialize(DeliveryPolicy.Config config,DeliveryPolicy.Revision baseline,Map<String,ExtraContent.Entry> roots)throws Exception {
  pinned=Collections.emptyMap();
  byte[] inventory;
  try {inventory=GameAssets.read(ExtraContent.bundled("bootstrap_inventory.json"),DeliveryPolicy.MAX_POINTER);}
  catch(FileNotFoundException absent){if(config.apk>=204)throw new IOException("Signed startup inventory is missing",absent);return;}
  Map<String,Object> value=DeliveryPolicy.map(DeliveryPolicy.Json.parse(inventory));
  if(!DeliveryPolicy.str(value,"schema").equals("ffbe-bootstrap-inventory-v1")
    ||!DeliveryPolicy.str(value,"package").equals(DeliveryPolicy.PACKAGE)
    ||!DeliveryPolicy.str(value,"signing_certificate_sha256").equals(DeliveryPolicy.SIGNER)
    ||DeliveryPolicy.num(value,"APK_version")!=config.apk
    ||DeliveryPolicy.num(value,"asset_version")!=baseline.version
    ||!DeliveryPolicy.str(value,"manifest_sha256").equals(baseline.id))throw new IOException("Signed startup inventory identity disagrees");
  Object values=value.get("assets");
  if(!(values instanceof List)||((List<?>)values).isEmpty()||((List<?>)values).size()>50000)throw new IOException("Complete startup inventory required");
  Set<String> expected=new LinkedHashSet<>();
  for(DeliveryPolicy.Asset asset:baseline.assets.values())if(asset.namespace.equals("root")&&asset.phase.equals("boot"))expected.add(asset.path);
  Map<String,ExtraContent.Entry> accepted=new LinkedHashMap<>();
  for(Object item:(List<?>)values){
   Map<String,Object> row=DeliveryPolicy.map(item);String path=DeliveryPolicy.str(row,"path");
   ExtraContent.Entry entry=roots.get(path);DeliveryPolicy.Asset asset=baseline.assets.get("root:"+path);
   if(!DeliveryPolicy.str(row,"namespace").equals("root")||!GameAssets.safePath(path)
     ||!DeliveryPolicy.str(row,"apk_path").equals("assets/"+path)
     ||entry==null||asset==null||!asset.phase.equals("boot")
     ||DeliveryPolicy.num(row,"bytes")!=entry.size||!DeliveryPolicy.str(row,"sha256").equals(entry.hash)
     ||accepted.put(path,entry)!=null)throw new IOException("Startup inventory disagrees with signed baseline: "+path);
  }
  if(!accepted.keySet().equals(expected))throw new IOException("Startup inventory is incomplete or has unlisted assets");
  // Validate every declared APK source before marking it available. The cache copy
  // and raw Android AssetManager source must agree with the signed manifest.
  for(ExtraContent.Entry entry:accepted.values())ExtraContent.seedBundled(entry);
  pinned=Collections.unmodifiableMap(accepted);
 }

 static boolean contains(ExtraContent.Entry entry){
  ExtraContent.Entry own=pinned.get(entry.path);return own!=null&&own.hash.equals(entry.hash)&&own.size==entry.size;
 }

 static void validateGraph(Map<String,ExtraContent.Entry> next)throws IOException {
  for(ExtraContent.Entry own:pinned.values()){
   ExtraContent.Entry entry=next.get(own.path);
   if(entry==null||!entry.hash.equals(own.hash)||entry.size!=own.size)throw new IOException("Bundled startup changes require a newer APK: "+own.path);
  }
 }
}
