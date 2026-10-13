package android.app;
import java.io.File;
import android.content.Context;
import android.content.res.AssetManager;
public class Application extends Context {
    private final File files;
    private final AssetManager assets;
    public Application(File files, File assets) { this.files = files; this.assets = new AssetManager(assets); }
    public File getFilesDir() { return files; }
    public AssetManager getAssets() { return assets; }
}
