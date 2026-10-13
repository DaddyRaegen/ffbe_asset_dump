"""Scoped BlueStacks state/screenshots; leaves all installed app data intact."""
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parent
ADB=Path(r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe')
SERIAL='emulator-5554'
def adb(*args,binary=False):
    r=subprocess.run([str(ADB),'-s',SERIAL,*args],capture_output=True,timeout=90)
    if r.returncode: raise RuntimeError(r.stderr.decode('utf-8','replace'))
    return r.stdout if binary else r.stdout.decode('utf-8','replace')
def screenshot(name):
    assert name.replace('-','').replace('_','').isalnum()
    image=adb('exec-out','screencap','-p',binary=True)
    assert image.startswith(b'\x89PNG\r\n\x1a\n')
    path=ROOT/(name+'.png');path.write_bytes(image)
    return str(path)
if __name__=='__main__':
    assert len(sys.argv)==2
    print(json.dumps({'serial':SERIAL,'screenshot':screenshot(sys.argv[1]),'foreground':adb('shell','dumpsys','window','windows').split('mCurrentFocus=')[-1].splitlines()[0]}))
