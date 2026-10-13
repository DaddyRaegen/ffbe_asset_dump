package O1;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.net.Uri;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Manifest notification only; never installs an APK or promotes a channel. */
public final class PatchUpdater {
 private static final AtomicBoolean checked=new AtomicBoolean();
 static boolean apkURL(String value,String channel){try{URL u=new URL(value);if(!"https".equals(u.getProtocol())||u.getUserInfo()!=null||(u.getPort()!=-1&&u.getPort()!=443)||u.getQuery()!=null||u.getRef()!=null||!u.getPath().endsWith(".apk"))return false;if(DeliveryPolicy.releaseURL(value)){String tail=u.getPath().substring(("/"+DeliveryPolicy.REPO+"/releases/download/").length()),tag=tail.substring(0,tail.indexOf('/'));return channel.equals("beta")?tag.startsWith("beta-"):!tag.startsWith("beta-");}return u.getHost().equals("ffbe.luminest.io")&&!u.getPath().contains("..")&&(channel.equals("beta")?u.getPath().startsWith("/downloads/beta/releases/"):u.getPath().startsWith("/downloads/")&&!u.getPath().startsWith("/downloads/beta/"));}catch(Exception invalid){return false;}}
 static String notificationURL(byte[] bytes,DeliveryPolicy.Config config)throws Exception {
  if(bytes.length>65536)throw new IOException("Oversized APK notification manifest");Map<String,Object> m=DeliveryPolicy.map(DeliveryPolicy.Json.parse(bytes));Object enabled=m.get("apk_update_enabled");if(Boolean.FALSE.equals(enabled)||m.containsKey("apk_update_enabled")&&!(enabled instanceof Boolean))return null;
  if(!DeliveryPolicy.str(m,"channel").equals(config.channel)||!DeliveryPolicy.str(m,"package").equals(DeliveryPolicy.PACKAGE)||DeliveryPolicy.num(m,"versionCode")<=config.apk)return null;String apk=DeliveryPolicy.str(m,"apk_url");if(!apkURL(apk,config.channel)||!DeliveryPolicy.str(m,"sha256").matches("[a-f0-9]{64}")||DeliveryPolicy.num(m,"bytes")<1)return null;return apk;
 }
 public static void check(){if(!checked.compareAndSet(false,true))return;new Thread(new Runnable(){public void run(){try{
  final DeliveryPolicy.Config config=GameAssets.configuration();if(config==null)return;
  HttpURLConnection c=(HttpURLConnection)new URL(config.updater).openConnection();byte[] bytes;try{c.setConnectTimeout(8000);c.setReadTimeout(8000);c.setInstanceFollowRedirects(false);c.setUseCaches(false);if(c.getResponseCode()!=200)return;bytes=GameAssets.read(c.getInputStream(),65536);}finally{c.disconnect();}
  final String apk=notificationURL(bytes,config);if(apk==null)return;
  final Activity activity=(Activity)Class.forName("com.square_enix.ffbejpn.Lapis").getMethod("getActivity").invoke(null);if(activity==null||activity.isFinishing())return;
  activity.runOnUiThread(new Runnable(){public void run(){if(activity.isFinishing())return;new AlertDialog.Builder(activity).setTitle("APK update available").setMessage("A newer FFBE Memorial "+config.channel+" APK is available. Install it over the existing app to keep saved data and completed downloads.").setPositiveButton("Open download",new DialogInterface.OnClickListener(){public void onClick(DialogInterface d,int which){activity.startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(apk)));}}).setNegativeButton("Later",null).show();}});
 }catch(Exception unavailable){/* Optional check never blocks verified offline play. */}}},"FFBE-APK-Version-Check").start();}
}
