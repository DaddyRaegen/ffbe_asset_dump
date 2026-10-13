"""Read exact retained productionPatch5 script updater constants; no network."""
from pathlib import Path
import hashlib,json,re,zipfile
ROOT=Path(__file__).resolve().parents[1]
APK=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-09-29-units-cards-ios\dist\FFBE-Memorial-EN-Patch-5-Units-Cards.apk')
with zipfile.ZipFile(APK) as archive:script=archive.read('assets/frida_script.js')
text=script.decode('utf-8')
matches=[]
for pattern in [r'^.*JAVA_CLASS.*$',r'^.*PATCH_VERSION.*$',r'^.*MANIFEST_URL.*$',r'^.*DOWNLOAD_URL.*$',r'^.*checkForUpdate.*$']:
 matches.extend(re.findall(pattern,text,re.M))
value={'APK':str(APK),'script_sha256':hashlib.sha256(script).hexdigest(),'updater_lines':matches,'network_requests_made':0,'device_actions':False}
(ROOT/'audit').mkdir(parents=True,exist_ok=True)
(ROOT/'audit/PATCH5_UPDATER_SCRIPT.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps(value))
