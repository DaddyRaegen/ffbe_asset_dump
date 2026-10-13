package O1;

import java.io.*;
import java.lang.reflect.Method;
import java.security.MessageDigest;

/** Versioned, verified battle-table overrides; all other assets use the CDN resolver. */
public final class BattleTables {
    private static String sourceHash(String name) {
        if ("3Lc1DWQV.dat".equals(name)) return "7e1844956b214e30d3fe150633246e11858a9df99f402d592e1d96fa6f64154c";
        if ("4F1Zpy7V.dat".equals(name)) return "ec6f675a3fde022a73f5bd00d50d28332be45e856c24183265d8873e92cd7d25";
        if ("6J8jwSDW.dat".equals(name)) return "b5007563daedcd0015bba52ec19be223f9a8d1ec0aae93c4c8d56eac9a13c5df";
        if ("7FGj2bCh.dat".equals(name)) return "8f469f1e4168698357cafe30ff8941e524ce4d18ec930c111dbb0726b5dda39c";
        if ("8qbVQUx5.dat".equals(name)) return "527d44534ea2ef0dd8a85f69378927f717a34df91b5438e3450c1722f8088176";
        if ("BrjD06sM.dat".equals(name)) return "0787e5a5067643374b5c474d523d73ed9c96e213bed227c55aeee0f8fc320fed";
        if ("QH70YTbz.dat".equals(name)) return "6a857fbde85ad92b0004a1a96e6addf58eaf4c8a3bb5cb6d71838cbc416c8c91";
        if ("TK61DudV.dat".equals(name)) return "96cd54f84e5dc940320b7e0848c57b3ee6c7bffe7fdad4da72425ae983e827a1";
        if ("Y3H1q2XS.dat".equals(name)) return "02eb9c75f14d31ffd0dbfb3ae3f5d655f72cc15c90fadeb0abebdb48c907f2a7";
        if ("c5T4PIyL.dat".equals(name)) return "112c9b055ff147d870a616168d4dd50f33c6d410b2e9fcc3668351ae14e6bede";
        if ("jTGeKc87.dat".equals(name)) return "12413d72fb1353c57c4eed2b1f323da91ceb25acf63d2bc68c59c9408bbbba83";
        if ("jqv20D3o.dat".equals(name)) return "5a77bbdaeb3bce89b71135ab7e29d28bfc67e482da9648e536e0b825f3fd8cc9";
        if ("sd1a2bPL.dat".equals(name)) return "65c6c2ad5960f4ade64b58f7cf23478c6e5f51fb2465cf5e4be67e696cd8a0d0";
        if ("wJE09yxD.dat".equals(name)) return "08e47c2feb9697e732158c806c81523c113e091327f1e82be9759a4756c54151";
        return null;
    }
    private static String translationHash(String name) {
        if ("3Lc1DWQV.dat".equals(name)) return "74aa4cbd9ed69ac3edd5dd2b1f5523911e59158a2ce62fbbbb07db174b9fac84";
        if ("4F1Zpy7V.dat".equals(name)) return "d3ac9f9d2e02775df187b1a4991a96589788f3e815c01a0ffe9fc5d0897e13ae";
        if ("6J8jwSDW.dat".equals(name)) return "9850a0cbda83f55555c784321ff50f835c53793b30fbbd48611c6cfd973187cf";
        if ("7FGj2bCh.dat".equals(name)) return "e99ceaa224bdb0db39d77da40b32a948c72c9662a4c52468ac77d62f409a1135";
        if ("8qbVQUx5.dat".equals(name)) return "e29dc591cc71768dbbce460b03ac45a240b30b6ae60b8fe23575d67d9e43a0f7";
        if ("BrjD06sM.dat".equals(name)) return "71b2eb2baa19c89a342c6b0a9f6d2c0fc594597793fcfbb2ba04fd38808645b1";
        if ("QH70YTbz.dat".equals(name)) return "07caa8c825ce838f5f68b43ad232212de864691618573d5a091ea9bcfecd322d";
        if ("TK61DudV.dat".equals(name)) return "31eadf7985aaec05dadcef035016d4c9bce9a2a6c525a1a77d7c761eaf3956d0";
        if ("Y3H1q2XS.dat".equals(name)) return "7c27dfa10401cd181f82638454149bf90e1a80d57168ed1b2684bc358eaa0ba2";
        if ("c5T4PIyL.dat".equals(name)) return "fc865a7d81461c7f729e6312601077e11acc116f3475f0d60aa2ae7bb6b3caf5";
        if ("jTGeKc87.dat".equals(name)) return "1599ed3ef458d047b9fbb46944c470837a4d7cf8446d8675305f24c09c52428f";
        if ("jqv20D3o.dat".equals(name)) return "a7cd7b2b8ddd80aad7c356dc5bf2791e827a8d92c9ccdc3c36960d52e8f0c931";
        if ("sd1a2bPL.dat".equals(name)) return "4aab9dc2942ed90dc9bdfc6cbefa53ca563de14ddaba4689a362b05dbf299208";
        if ("wJE09yxD.dat".equals(name)) return "e554c1d344a8eb226d218e7555d82aca0bdb62cd4ad1405c783ddbff13fb1877";
        return null;
    }

    public static synchronized String choose(String name, String originalPath) {
        String originalHash = sourceHash(name);
        if (originalHash == null || originalPath == null || originalPath.length() == 0) return originalPath;
        try {
            // Never mask a future CDN revision or an unexpected local source table.
            if (!originalHash.equals(hash(new FileInputStream(originalPath)))) return originalPath;
            Object app = Class.forName("android.app.ActivityThread")
                .getMethod("currentApplication").invoke(null);
            if (app == null) return originalPath;
            Class<?> context = Class.forName("android.content.Context");
            File files = (File) context.getMethod("getFilesDir").invoke(app);
            String expected = translationHash(name);
            File dir = new File(files, "battle/r8/" + expected);
            if (!dir.isDirectory() && !dir.mkdirs()) return originalPath;
            File out = new File(dir, name);
            if (out.isFile() && expected.equals(hash(new FileInputStream(out)))) return out.getAbsolutePath();
            Object assets = context.getMethod("getAssets").invoke(app);
            Method open = Class.forName("android.content.res.AssetManager").getMethod("open", String.class);
            InputStream in = ExtraContent.open("battle/" + name);
            File temporary = new File(dir, name + ".tmp");
            try {
                FileOutputStream stream = new FileOutputStream(temporary);
                try {
                    byte[] buffer = new byte[8192]; int n;
                    while ((n = in.read(buffer)) != -1) stream.write(buffer, 0, n);
                    stream.getFD().sync();
                } finally { stream.close(); }
            } finally { in.close(); }
            if (!expected.equals(hash(new FileInputStream(temporary)))) {
                temporary.delete();
                return originalPath;
            }
            if (out.exists() && !out.delete()) return originalPath;
            if (!temporary.renameTo(out)) return originalPath;
            return out.getAbsolutePath();
        } catch (Exception e) {
            return originalPath;
        } catch (LinkageError e) {
            return originalPath;
        }
    }

    private static String hash(InputStream in) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try {
            byte[] buffer = new byte[8192]; int n;
            while ((n = in.read(buffer)) != -1) digest.update(buffer, 0, n);
        } finally { in.close(); }
        StringBuilder result = new StringBuilder(64);
        for (byte b : digest.digest()) {
            int value = b & 255;
            if (value < 16) result.append('0');
            result.append(Integer.toHexString(value));
        }
        return result.toString();
    }
}
