package android.content.res;
import java.io.*;
public class AssetManager {
    private final File root;
    public AssetManager(File root) { this.root = root; }
    public InputStream open(String path) throws IOException { return new FileInputStream(new File(root, path)); }
}
