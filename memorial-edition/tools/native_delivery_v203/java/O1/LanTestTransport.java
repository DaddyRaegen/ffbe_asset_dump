package O1;
import java.net.URL;

/** Disabled in production. A dedicated LAN build pins one private IPv4 origin at compile time. */
public final class LanTestTransport {
    public static final String ORIGIN="";
    private LanTestTransport(){}
    static boolean allowed(String value){try{return allowed(new URL(value));}catch(Exception invalid){return false;}}
    static boolean allowed(URL url){
        if(ORIGIN.isEmpty())return false;
        try {
            URL pinned=new URL(ORIGIN);
            if(!pinned.getProtocol().equals("http")||pinned.getPort()<1||pinned.getPort()>65535
                ||pinned.getUserInfo()!=null||pinned.getQuery()!=null||pinned.getRef()!=null||!pinned.getPath().isEmpty())return false;
            String[] address=pinned.getHost().split("\\.",-1);if(address.length!=4)return false;
            int[] octet=new int[4];for(int i=0;i<4;i++){if(!address[i].matches("0|[1-9][0-9]{0,2}"))return false;octet[i]=Integer.parseInt(address[i]);if(octet[i]>255)return false;}
            if(!(octet[0]==10||octet[0]==127||(octet[0]==192&&octet[1]==168)||(octet[0]==172&&octet[1]>=16&&octet[1]<=31)))return false;
            return url.getProtocol().equals(pinned.getProtocol())&&url.getHost().equals(pinned.getHost())&&url.getPort()==pinned.getPort()
                &&url.getUserInfo()==null&&url.getQuery()==null&&url.getRef()==null
                &&url.getPath().matches("/ffbe-content/(base|content|content-updates)/[A-Za-z0-9_./-]+")
                &&!url.getPath().contains("..")&&!url.getPath().contains("//");
        }catch(Exception invalid){return false;}
    }
}
