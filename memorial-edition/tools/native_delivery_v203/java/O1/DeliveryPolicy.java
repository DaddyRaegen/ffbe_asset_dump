package O1;
import java.io.*;
import java.net.*;
import java.security.MessageDigest;
import java.util.*;

/** Pure-Java release and catalog admission rules shared with deterministic host checks. */
public final class DeliveryPolicy {
 public static final String REPO="luminest-llc/ffbe-memorial-downloads";
 public static final String ENGINE="ffbe-native-delivery-v203";
 public static final String PACKAGE="com.square_enix.ffbejpn",SIGNER="21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee";
 public static final int MAX_CATALOG=8*1024*1024,MAX_POINTER=4*1024*1024;
 public static final class Config {
  public final String channel,rootHash,contentHash,updater,pointer;
  public final long version,apk;
  public Config(byte[] bytes,byte[] root,byte[] content)throws Exception {
   String s=new String(bytes,"UTF-8");String[] ll=s.split("\n",-1);
   if(ll.length!=3||!ll[0].equals("ffbe-delivery-release-v1")||!ll[2].isEmpty()||s.indexOf('\r')>=0||s.indexOf('\0')>=0)throw new IOException("Invalid release metadata");
   String[] p=ll[1].split("\t",-1);if(p.length!=7)throw new IOException("Invalid release metadata fields");
   channel=p[0];version=Long.parseLong(p[1]);apk=Long.parseLong(p[2]);rootHash=p[3];contentHash=p[4];updater=p[5];pointer=p[6];
   if(!(channel.equals("beta")||channel.equals("prod"))||version<1||apk<203||!rootHash.equals(hash(root))||!contentHash.equals(hash(content)))throw new IOException("Incompatible release baseline");
   if(!updater.equals(metadataURL(channel,"patch_version.json"))||!pointer.equals(metadataURL(channel,"manifest.json")))throw new IOException("Cross-channel manifest rejected");
  }
 }
 public static final class Catalog {
  public final String hash,url;public final long bytes;
  Catalog(Object object)throws Exception {
   Map<String,Object> m=map(object);hash=str(m,"sha256");url=str(m,"url");bytes=num(m,"bytes");
   if(!hash.matches("[a-f0-9]{64}")||bytes<1||bytes>MAX_CATALOG||!releaseURL(url))throw new IOException("Invalid immutable catalog");
  }
 }
 public static final class Revision {
  public final long version,minAPK;public final Catalog root,content,base;public final byte[] descriptor;public final String id;
  public final Map<String,Asset> assets=new LinkedHashMap<>();
  public Revision(byte[] bytes,Config config,String baseHash,long baseBytes)throws Exception {
   if(bytes.length>MAX_POINTER)throw new IOException("Oversized asset manifest");Map<String,Object> m=map(Json.parse(bytes));
   if(!str(m,"schema").equals("ffbe-asset-manifest-v1")||!str(m,"channel").equals(config.channel)||!str(m,"engine_compat").equals(ENGINE)||!str(m,"package").equals(PACKAGE)||!str(m,"signing_certificate_sha256").equals(SIGNER))throw new IOException("Incompatible asset identity, channel or engine");
   version=num(m,"asset_version");minAPK=num(m,"APK_min_version");root=new Catalog(m.get("root_catalog"));content=new Catalog(m.get("content_catalog"));base=new Catalog(m.get("base_catalog"));
   if(version<1||minAPK<1||!base.hash.equals(baseHash)||base.bytes!=baseBytes)throw new IOException("Base catalog requires an APK update");
   Object values=m.get("assets");if(!(values instanceof List)||((List<?>)values).isEmpty()||((List<?>)values).size()>50000)throw new IOException("Complete per-asset metadata required");
   for(Object value:(List<?>)values){Asset asset=new Asset(value,version);if(assets.put(asset.id(),asset)!=null)throw new IOException("Duplicate per-asset identity");}
   descriptor=bytes;id=hash(bytes);
  }
  public void verifyCatalogs(byte[] rootBytes,byte[] contentBytes,byte[] baseBytes)throws Exception{
   if(rootBytes.length!=root.bytes||contentBytes.length!=content.bytes||baseBytes.length!=base.bytes||!hash(rootBytes).equals(root.hash)||!hash(contentBytes).equals(content.hash)||!hash(baseBytes).equals(base.hash))throw new IOException("Asset descriptor catalog pins disagree");
   Set<String> expected=new HashSet<>();
   for(String namespace:new String[]{"root","content"})for(ExtraContent.Entry entry:ExtraContent.parseCatalog(namespace.equals("root")?rootBytes:contentBytes).values()){
    String key=namespace+":"+entry.path;Asset asset=assets.get(key);if(asset==null||!asset.matches(entry.hash,entry.size,entry.url,entry.offset,entry.wireSize,entry.method,entry.sourceSize))throw new IOException("Per-asset metadata disagrees with content catalog: "+key);expected.add(key);
    if(namespace.equals("root")&&!asset.phase.equals(entry.path.startsWith("side_stories/")?"game":"boot"))throw new IOException("Invalid boot dependency phase");
   }
   try(BufferedReader reader=new BufferedReader(new InputStreamReader(new ByteArrayInputStream(baseBytes),"UTF-8"))){if(!"ffbe-base-v1".equals(reader.readLine()))throw new IOException("Invalid base catalog");String line;while((line=reader.readLine())!=null){String[] p=line.split("\t",-1);if(p.length!=5)throw new IOException("Invalid base row");CdnDownloader.FileEntry entry=new CdnDownloader.FileEntry(p);String key="base:"+entry.pack+"/"+entry.name;Asset asset=assets.get(key);if(!expected.add(key)||asset==null||!asset.matches(entry.hash,entry.size,entry.url,0,entry.size,0,entry.size))throw new IOException("Per-asset metadata disagrees with base catalog: "+key);}}
   if(!expected.equals(assets.keySet()))throw new IOException("Per-asset metadata is incomplete or contains unlisted files");
  }
  public void validateNext(Revision previous)throws IOException{
   if(version<previous.version||!assets.keySet().containsAll(previous.assets.keySet()))throw new IOException("Asset metadata regresses preserved identities");
   for(Asset old:previous.assets.values()){Asset next=assets.get(old.id());if(next.version<old.version||(!next.hash.equals(old.hash)||next.bytes!=old.bytes)&&next.version<=old.version)throw new IOException("Per-file data changes require a newer revision: "+old.id());}
  }
 }
 public static final class Asset {
  public final String namespace,path,hash,url,phase;public final long version,bytes,offset,wire,source;public final int method;
  Asset(Object value,long graphVersion)throws Exception{Map<String,Object> m=map(value),t=map(m.get("transport"));namespace=str(m,"namespace");path=str(m,"path");hash=str(m,"sha256");version=num(m,"version");bytes=num(m,"bytes");url=str(t,"url");offset=num(t,"offset");wire=num(t,"wire_bytes");source=num(t,"source_bytes");long kind=num(t,"method");method=(int)kind;phase=namespace.equals("root")?str(m,"phase"):"game";
   if(!(namespace.equals("root")||namespace.equals("content")||namespace.equals("base"))||!(namespace.equals("base")?path.matches("on_demand_asset[2-6]?/[A-Za-z0-9_.-]+")&&!path.contains(".."):GameAssets.safePath(path))||!hash.matches("[a-f0-9]{64}")||version<1||version>graphVersion||bytes<1||offset<0||wire<1||offset>source-wire||(kind!=0&&kind!=8)||!payloadURL(url))throw new IOException("Invalid per-asset data or transport");ResumableTransfer.validateSource(url,source);
  }
  String id(){return namespace+":"+path;}
  boolean matches(String h,long b,String u,long o,long w,int m,long s){return hash.equals(h)&&bytes==b&&url.equals(u)&&offset==o&&wire==w&&method==m&&source==s;}
 }
 public static String metadataURL(String channel,String name){return "https://raw.githubusercontent.com/"+REPO+"/"+(channel.equals("beta")?"beta":"main")+"/channels/"+channel+"/"+name;}
 public static boolean releaseURL(String value){
  try{URL u=new URL(value);return "https".equals(u.getProtocol())&&u.getUserInfo()==null&&(u.getPort()==-1||u.getPort()==443)&&u.getQuery()==null&&u.getRef()==null&&u.getHost().equals("github.com")&&u.getPath().matches("/"+REPO+"/releases/download/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+");}catch(Exception e){return false;}
 }
 public static boolean payloadURL(String value){int fragment=value.indexOf('#');String source=fragment<0?value:value.substring(0,fragment);if(!releaseURL(source))return false;return fragment<0||value.substring(fragment).matches("#ffbe-range=[0-9]+:[0-9]+:[0-9]+");}
 public static String hash(byte[] bytes)throws Exception {StringBuilder b=new StringBuilder(64);for(byte x:MessageDigest.getInstance("SHA-256").digest(bytes))b.append(String.format(Locale.ROOT,"%02x",x&255));return b.toString();}
 public static Map<String,Object> map(Object value)throws IOException {if(!(value instanceof Map))throw new IOException("JSON object required");return (Map<String,Object>)value;}
 public static String str(Map<String,Object> m,String k)throws IOException {Object o=m.get(k);if(!(o instanceof String))throw new IOException("Invalid "+k);return (String)o;}
 public static long num(Map<String,Object> m,String k)throws IOException {Object o=m.get(k);if(!(o instanceof Long))throw new IOException("Invalid "+k);return (Long)o;}
 static final class Json {
  final String s;int at,nodes;
  Json(byte[] b)throws Exception{s=new String(b,"UTF-8");if(s.indexOf('\0')>=0)throw new IOException("NUL in JSON");}
  static Object parse(byte[] b)throws Exception {Json j=new Json(b);Object o=j.value(0);j.ws();if(j.at!=j.s.length())throw new IOException("Trailing JSON");return o;}
  void ws(){while(at<s.length()&&" \t\r\n".indexOf(s.charAt(at))>=0)at++;}
  Object value(int depth)throws Exception {
   ws();if(depth>32||++nodes>500000||at>=s.length())throw new IOException("Invalid JSON bounds");char c=s.charAt(at);
   if(c=='{'){at++;Map<String,Object> m=new LinkedHashMap<>();ws();if(take('}'))return m;do{ws();String k=string();ws();if(!take(':'))throw new IOException("Missing colon");Object v=value(depth+1);if(m.containsKey(k))throw new IOException("Duplicate JSON field");m.put(k,v);ws();if(take('}'))return m;}while(take(','));throw new IOException("Invalid object");}
   if(c=='['){at++;List<Object> l=new ArrayList<>();ws();if(take(']'))return l;do{l.add(value(depth+1));ws();if(take(']'))return l;}while(take(','));throw new IOException("Invalid array");}
   if(c=='"')return string();
   for(String k:new String[]{"true","false","null"})if(s.startsWith(k,at)){at+=k.length();return k.equals("null")?null:Boolean.valueOf(k);}
   int begin=at;if(c=='-')at++;while(at<s.length()&&Character.isDigit(s.charAt(at)))at++;String number=s.substring(begin,at);if(!number.matches("-?(0|[1-9][0-9]*)"))throw new IOException("Integer JSON number required");return Long.valueOf(number);
  }
  boolean take(char c){if(at<s.length()&&s.charAt(at)==c){at++;return true;}return false;}
  String string()throws Exception {
   if(!take('"'))throw new IOException("String required");StringBuilder b=new StringBuilder();while(at<s.length()){char c=s.charAt(at++);if(c=='"')return b.toString();if(c<32)throw new IOException("Invalid JSON control");if(c=='\\'){if(at>=s.length())throw new IOException("Invalid escape");c=s.charAt(at++);switch(c){case '"':case '\\':case '/':break;case 'b':c='\b';break;case 'f':c='\f';break;case 'n':c='\n';break;case 'r':c='\r';break;case 't':c='\t';break;case 'u':if(at+4>s.length())throw new IOException("Invalid unicode");c=(char)Integer.parseInt(s.substring(at,at+4),16);at+=4;break;default:throw new IOException("Invalid escape");}}b.append(c);}throw new IOException("Unterminated string");
  }
 }
}
