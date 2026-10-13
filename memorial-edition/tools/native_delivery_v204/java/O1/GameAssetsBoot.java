package O1;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.widget.*;
import android.view.View;
import java.util.*;

/** Verify the packaged startup baseline before native launch; remaining files use the native UI. */
public final class GameAssetsBoot extends Activity {
 private TextView text;private ProgressBar bar;private Button button;
 private final Handler handler=new Handler();private volatile boolean destroyed,working;
 private volatile List<ExtraContent.Entry> pending=Collections.emptyList();private volatile long total;
 private volatile String status="Preparing packaged startup files.";
 private final Runnable refresh=new Runnable(){public void run(){if(destroyed)return;long received=0;for(ExtraContent.Entry e:pending)received+=e.transferred;text.setText(status);bar.setIndeterminate(total==0);if(total>0){bar.setMax(1000);bar.setProgress((int)Math.min(1000,received*1000/total));}handler.postDelayed(this,200);}};
 public static void redirect(Activity a){a.startActivity(new Intent().setClassName(a,"O1.GameAssetsBoot"));a.finish();}
 @Override public void onCreate(Bundle state){super.onCreate(state);LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);layout.setPadding(32,48,32,32);TextView title=new TextView(this);title.setText("FFBE Memorial");title.setTextSize(26);layout.addView(title);text=new TextView(this);text.setTextSize(17);layout.addView(text);bar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);layout.addView(bar);button=new Button(this);button.setText("Checking startup files");button.setEnabled(false);layout.addView(button);setContentView(layout);button.setOnClickListener(new View.OnClickListener(){public void onClick(View v){begin(true);}});handler.post(refresh);begin(false);}
 private void begin(final boolean consent){if(working||destroyed)return;working=true;button.setEnabled(false);new Thread(new Runnable(){public void run(){try{pending=ContentDownloader.checkBootAssets();total=0;for(ExtraContent.Entry e:pending)total+=e.wireSize;
  if(!pending.isEmpty()&&!consent){status="Startup files need to be downloaded before the game can draw its download screen.\n\nOnly missing or changed files are downloaded; saved partial downloads resume. Remaining game files use the game’s download screen.\n\nStartup download: "+String.format(Locale.US,"%.1f MB",total/1000000.0);runOnUiThread(new Runnable(){public void run(){if(destroyed)return;button.setText("Download startup files");button.setEnabled(true);}});return;}
  status="Preparing startup files.";ContentDownloader.downloadBootAssets(new ExtraContent.ProgressListener(){public void changed(List<ExtraContent.Entry> list,long bytes){pending=list;total=bytes;}});
  status="Opening the game.";runOnUiThread(new Runnable(){public void run(){if(destroyed)return;startActivity(new Intent().setClassName(GameAssetsBoot.this,"com.square_enix.ffbejpn.Lapis"));finish();}});
 }catch(final Exception failure){status="Download paused. Your verified files and partial downloads are kept.\n\nCheck your connection and free storage, then resume.";runOnUiThread(new Runnable(){public void run(){if(destroyed)return;button.setText("Resume");button.setEnabled(true);}});}finally{working=false;}}},"FFBE-Startup-Files").start();}
 @Override public void onDestroy(){destroyed=true;handler.removeCallbacks(refresh);super.onDestroy();}
}
