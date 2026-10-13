package android.content.res;
import java.io.*;
public class AssetManager {
 private final File root;public AssetManager(File root){this.root=root;}
 public InputStream open(String name)throws IOException{return new FileInputStream(new File(root,name));}
 public AssetFileDescriptor openFd(String name)throws IOException{throw new IOException("not used in host fixture");}
 public String[] list(String dir)throws IOException{String[] files=new File(root,dir).list();return files==null?new String[0]:files;}
}
