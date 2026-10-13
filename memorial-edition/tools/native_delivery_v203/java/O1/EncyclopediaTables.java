package O1;

import java.io.*;
import java.lang.reflect.Method;
import java.security.MessageDigest;

/** Versioned, verified encyclopedia-table overrides; all other assets use the CDN resolver. */
public final class EncyclopediaTables {
    private static String sourceHash(String name) {
        if ("1r6jb9wB.dat".equals(name)) return "2aa0fddc452c436ad847c15ad47fcca69677cfe7b6324ab7bb68d86eca9ef666";
        if ("Da62x85q.dat".equals(name)) return "3cc77aad4928c823c5af384d29631d51c1a7d00254e3f5a100ff4dde3f55fd69";
        if ("G9K8kLXz.dat".equals(name)) return "4dedf0eb32642451f11165971baecd0836c51e20222f45440c727017979342e0";
        if ("SsidX62G.dat".equals(name)) return "1d9cac7085824fc8e959c19613908d2a0e19775567a689fb0e42ac7fb90c6ce0";
        if ("Svq1K0rh.dat".equals(name)) return "ca92f963ae1187e94643e52973ed5e155be89218fc297b758f7bd1861300dd6b";
        if ("WF57bvfG.dat".equals(name)) return "dab2d867545321f00ee9d58d8e5847034f9b56cb0ecc7f5ef38665322df959db";
        if ("jTGeKc87.dat".equals(name)) return "517dffa68f24f51e71497653574988272645a1a9ebbead2207a845082acf4a6c";
        if ("y8G2PKDk.dat".equals(name)) return "45d9880acbe221ad09fd0b00d42de01ed92251e6efed14d7a49ebf9819e7b2c3";
        if ("zE1hx53P.dat".equals(name)) return "5d47e9ef2afd9d9c68e8856207ef4bc2305c83e1cfde7d49e0e0e96465367723";
        return null;
    }
    private static String translationHash(String name) {
        if ("1r6jb9wB.dat".equals(name)) return "a12e23e0b76334dabfe07c906a02dc4238573042a0c880339eccffcae9875e30";
        if ("Da62x85q.dat".equals(name)) return "068d41672b5ef47620a411df5d64dbc08ffcc89db06e4eb77b94532d360aa44e";
        if ("G9K8kLXz.dat".equals(name)) return "9c3f9d4e17586b9bcf1deaff0d9b5c5deafa8f7adf1b9c58b8b06a8ea451ecf8";
        if ("SsidX62G.dat".equals(name)) return "b4dff6aed493fc5ea39635896e9654049109fd25cc3d0de6f1e1b3c739e74bd2";
        if ("Svq1K0rh.dat".equals(name)) return "198dd83a1c8cd442d71ff1b08f1fd58ea5bc25c010c73a3ecb392c45903a7c1c";
        if ("WF57bvfG.dat".equals(name)) return "63681530bfcc9373472890ecb0fa7ac80ed7f7e600065cd102fedcbc10ab841e";
        if ("jTGeKc87.dat".equals(name)) return "12413d72fb1353c57c4eed2b1f323da91ceb25acf63d2bc68c59c9408bbbba83";
        if ("y8G2PKDk.dat".equals(name)) return "9bc258ca557cff163a155a72995c204fb0e7b15b75fb58648b58a1240f3a7b73";
        if ("zE1hx53P.dat".equals(name)) return "b36943c69e0c67b178022623e4a90fb75afc6a2140c02e47d54912f43fdb9aec";
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
            File dir = new File(files, "encyclopedia/r7/" + expected);
            if (!dir.isDirectory() && !dir.mkdirs()) return originalPath;
            File out = new File(dir, name);
            if (out.isFile() && expected.equals(hash(new FileInputStream(out)))) return out.getAbsolutePath();
            Object assets = context.getMethod("getAssets").invoke(app);
            Method open = Class.forName("android.content.res.AssetManager").getMethod("open", String.class);
            InputStream in = ExtraContent.open("encyclopedia/" + name);
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
