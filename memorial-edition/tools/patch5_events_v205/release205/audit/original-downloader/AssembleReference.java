import java.io.File;
import java.nio.file.*;
import brut.androlib.smali.SmaliBuilder;
import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.writer.builder.DexBuilder;
import com.android.tools.smali.dexlib2.writer.io.FileDataStore;
/** Invoke the retained APK builder's own assembler for an isolated two-class fixture. */
public class AssembleReference {
 public static void main(String[] args)throws Exception{
  DexBuilder dex=new DexBuilder(new Opcodes(21));SmaliBuilder assembler=new SmaliBuilder(21);
  try(java.util.stream.Stream<Path> files=Files.walk(Paths.get(args[0]))){
   for(Path file:(Iterable<Path>)files.filter(p->p.toString().endsWith(".smali"))::iterator)
    if(!assembler.buildFile(file.toFile(),dex))throw new IllegalStateException("Assembly failed: "+file);
  }
  dex.writeTo(new FileDataStore(new File(args[1])));
 }
}
