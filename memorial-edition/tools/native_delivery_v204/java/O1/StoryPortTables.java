package O1;

import java.io.*;
import java.lang.reflect.Method;
import java.security.MessageDigest;

/** Versioned, verified battle-table overrides; all other assets use the CDN resolver. */
public final class StoryPortTables {
    private static boolean knownSource(String name,String actual) {
        if(actual.equals(sourceHash(name)))return true;
        if("24Eka6wL.dat".equals(name)&&"430954363a29bdad7852635cf2516894cf9e97799740360aaa8808b1502b7c95".equals(actual))return true;
        if("Fvix6V0n.dat".equals(name)&&"12a399f8d9c76ca632f8b90e5e81695f6e075689c3c6bfe660c67c24ce51f354".equals(actual))return true;
        return false;
    }

    /** Rebuild only imported tables' lazy indexes once for each payload revision. */
    public static synchronized void prepareIndexes() {
        try {
            Object app=Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null);
            if(app==null)return;
            File files=(File)Class.forName("android.content.Context").getMethod("getFilesDir").invoke(app);
            prepareMovie(files);
            for(String name:new String[]{"Nm36woZx.dat","9Zdr5ap0.dat","IL78hX09.dat","YW9MUm2H.dat","91vNbdxg.dat","B7LnP2TH.dat","24Eka6wL.dat","1Bj4oy5Q.dat","Fvix6V0n.dat","LM1APs6u.dat"}) {
                String version=translationHash(name);
                File marker=new File(files,"story_ports/index-"+version+".ready");
                if(marker.isFile())continue;
                File index=new File(files,name.substring(0,name.length()-4)+".i");
                File backup=new File(files,"story_ports/index-"+version+".backup");
                if(!marker.getParentFile().isDirectory()&&!marker.getParentFile().mkdirs())continue;
                if(index.isFile()&&!index.renameTo(backup))continue;
                marker.createNewFile();
            }
        } catch(Exception ignored) { }
    }
    /** The native story movie player reads this fixed private-files path. */
    private static void prepareMovie(File files) throws Exception {
        String name="SLB_LDA.usm";
        ExtraContent.load();ExtraContent.Entry entry=ExtraContent.current().get("story_ports/"+name);if(entry==null)return;File source=ExtraContent.available(entry,ExtraContent.current());if(source==null)return;
        MovieAssets.prepare(name,source,entry.hash,translationHash(name));
    }

    private static String sourceHash(String name) {
        if ("Nm36woZx.dat".equals(name)) return "de75c6d9ad07d773f0fc8099d323674142b619beff628beb8fbc4084eefdd083";
        if ("9Zdr5ap0.dat".equals(name)) return "22e185fac4e278e68eab7904d642c59fef12b234fd8d7bc8a35a0c1748b7d136";
        if ("IL78hX09.dat".equals(name)) return "63d77fa774eef7ec436267e3386cb077bfe50307cd4ca4933870410c69fbb705";
        if ("YW9MUm2H.dat".equals(name)) return "538f2b6f5e963a129aa0890f83967736df50c55a77bda0df1d877145e916f621";
        if ("91vNbdxg.dat".equals(name)) return "8a5160b92970eb91b831eeb7c16d1780b63ab5a45f5d869ea18ef068b4ce2283";
        if ("B7LnP2TH.dat".equals(name)) return "a2de41cac680671186f54de55b19ceaa305ba663cd98a3ee715aa12f0d68df02";
        if ("24Eka6wL.dat".equals(name)) return "7f7d3976d2ad52346ea238bfc28fbe4cbba294242c6f2ada6f4fc6023fb66375";
        if ("1Bj4oy5Q.dat".equals(name)) return "5bfe09dae3e0514609a692b9e32a0a4a737c7106fffe93b168914edf9222eda6";
        if ("Fvix6V0n.dat".equals(name)) return "a96030338290da0d80941d7ec6514c62caf30fe2b189eb4766feb4cf71c2b72c";
        if ("LM1APs6u.dat".equals(name)) return "518aec42a004b579cbd9f3601cc67512b6cf29b920f0461e6b6f38c7500421d7";
        if ("spdungeon9.cpk".equals(name)) return "00afddf1339bc13997c5770e16ef79353cd2ed2783ac93652a096f6b1a0de2b8";
        return null;
    }
    private static String translationHash(String name) {
        if ("Nm36woZx.dat".equals(name)) return "a14e374da14179e481e01d88ce4aa5fc3a3c7248f5580ba7a25d2fd15284332d";
        if ("9Zdr5ap0.dat".equals(name)) return "eb8d9abda712985f340c1cb401af2c3578ba5b2965527915120ec527ec4402d8";
        if ("IL78hX09.dat".equals(name)) return "90a2a77517d8b18e60e6ca4e4104ee9928475e8b1bcad1ea39c46ac0b094b8cf";
        if ("YW9MUm2H.dat".equals(name)) return "9f97b6f41fb45c4dbe34cc72a3e52c23b0a65439110f43ae03020f0f0c93c03c";
        if ("91vNbdxg.dat".equals(name)) return "322f13eb0a5f2140c5e893decd72fc9ebb304da4d9a9edb9961f6b448b90f578";
        if ("B7LnP2TH.dat".equals(name)) return "9fa07490839b3bde197a226321214a39879e26b639f44c82688dacf58f11ca85";
        if ("24Eka6wL.dat".equals(name)) return "ff8ce05f346f8ff02eac89b4df5a66514b4d49d9a527d5645508261ad54a4594";
        if ("1Bj4oy5Q.dat".equals(name)) return "9e8a88911fb3b536a3719acb32f7867b57b3bb5b31ea6a586590656f45db67cc";
        if ("Fvix6V0n.dat".equals(name)) return "22e44472374480de9e1ea159b85294d78ed1f3494b02e21642b1bfb70a7db3da";
        if ("LM1APs6u.dat".equals(name)) return "15f41fe1b662678ca7a365dc44e4b785398d3c1c85ead5622a52a4208e9157c3";
        if ("spdungeon9.cpk".equals(name)) return "4f35c01ebc18aaada87baee102156fbed0dd3d4eadc81c91361f9b36771a8a6d";
        if ("900010.cpk".equals(name)) return "3ac67dd97e590ee1d7d341e9e6be9704791ebe7a0d74ae7d6b8ad09ef6b311ad";
        if ("90001002.cpk".equals(name)) return "63931fe8525d3cfc018cba87548b279ed0e30a508532b8d0bebbb8c131d8b6ac";
        if ("90001003.cpk".equals(name)) return "425268389d0390dbc34b470ab52c4185455e91db9f14d8bc497fbdb2b645d3b5";
        if ("90001004.cpk".equals(name)) return "1521c0c92299ab89d591f80bbd5bf38b97f532dcf6e3c1d348aef5df3c2003cf";
        if ("90001001.cpk".equals(name)) return "4aeed9cc1230f8ebc9641d6dbfd57bfcf6a80dbd34e3bb3948fb9415dd5d76cd";
        if ("90001005.cpk".equals(name)) return "76e60745517dd9e48cbb8a9ef0b78aeae778bf973e1bb981bf5d9e2cc188bf46";
        if ("SLB_LDA.usm".equals(name)) return "b712c3d7262cb3b30f15295245910520b876e036deae426d031d493b4c65c8e0";
        return null;
    }

    public static synchronized String choose(String name, String originalPath) {
        String originalHash = sourceHash(name);
        if (translationHash(name) == null) return originalPath;
        boolean addedAsset = originalHash == null;
        if (!addedAsset && (originalPath == null || originalPath.length() == 0)) return originalPath;
        try {
            // Never mask a future CDN revision or an unexpected local source table.
            if (!addedAsset && !knownSource(name,hash(new FileInputStream(originalPath)))) return originalPath;
            if (addedAsset && originalPath != null && new File(originalPath).isFile()) return originalPath;
            Object app = Class.forName("android.app.ActivityThread")
                .getMethod("currentApplication").invoke(null);
            if (app == null) return originalPath;
            Class<?> context = Class.forName("android.content.Context");
            File files = (File) context.getMethod("getFilesDir").invoke(app);
            String expected = translationHash(name);
            File dir = new File(files, "story_ports/pilot1/" + expected);
            if (!dir.isDirectory() && !dir.mkdirs()) return originalPath;
            File out = new File(dir, name);
            if (out.isFile() && expected.equals(hash(new FileInputStream(out)))) return out.getAbsolutePath();
            Object assets = context.getMethod("getAssets").invoke(app);
            Method open = Class.forName("android.content.res.AssetManager").getMethod("open", String.class);
            InputStream in = ExtraContent.open("story_ports/" + name);
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
