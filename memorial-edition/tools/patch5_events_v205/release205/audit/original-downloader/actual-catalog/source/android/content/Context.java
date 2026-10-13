package android.content;
import java.io.File;
import android.content.res.AssetManager;
public abstract class Context {
    public abstract File getFilesDir();
    public File getExternalFilesDir(String ignored){return new File(getFilesDir(),"external");}
    public abstract AssetManager getAssets();
}
