package android.util;
import java.io.*;
/** Host-only fixtures for both backup/base and modern .new commit styles. */
public class AtomicFile {
 public static boolean MODE_NEW_FILE;
 private final File base,backup,fresh;private final boolean modern;
 public AtomicFile(File file){base=file;backup=new File(file+".bak");fresh=new File(file+".new");modern=MODE_NEW_FILE;}
 public FileOutputStream startWrite()throws IOException {
  if(modern)return new FileOutputStream(fresh);
  if(base.exists()){if(backup.exists()){if(!base.delete())throw new IOException("delete failed");}else if(!base.renameTo(backup))throw new IOException("backup failed");}return new FileOutputStream(base);
 }
 public void finishWrite(FileOutputStream out){try{out.getFD().sync();out.close();if(modern){if(base.exists()&&!base.delete())throw new IOException("replace failed");if(!fresh.renameTo(base))throw new IOException("commit failed");}else if(backup.exists()&&!backup.delete())throw new IOException("delete failed");}catch(IOException e){throw new RuntimeException(e);}}
 public void failWrite(FileOutputStream out){try{out.close();}catch(IOException ignored){}if(modern){fresh.delete();return;}if(base.exists())base.delete();if(backup.exists())backup.renameTo(base);}
 public FileInputStream openRead()throws IOException{if(backup.exists()){if(base.exists()&&!base.delete())throw new IOException("delete failed");if(!backup.renameTo(base))throw new IOException("restore failed");}return new FileInputStream(base);}
}
