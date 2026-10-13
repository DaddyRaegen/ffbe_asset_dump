from pathlib import Path
import re,hashlib,json

CALLBACKS={'onCreate':'(Landroid/os/Bundle;)V','onPause':'()V','onResume':'()V','onDestroy':'()V','onStart':'()V','onStop':'()V','onWindowFocusChanged':'(Z)V','onActivityResult':'(IILandroid/content/Intent;)V','onRequestPermissionsResult':'(I[Ljava/lang/String;[I)V','onBackPressed':'()V'}
GAME_CONSUMERS={'com/square_enix/ffbejpn/FridaBootstrap','org/cocos2dx/lib/Cocos2dxHttpURLConnection','org/cocos2dx/lib/Cocos2dxMusic','org/cocos2dx/lib/Cocos2dxSound','org/cocos2dx/lib/Cocos2dxTypefaces','org/cocos2dx/lib/Cocos2dxVideoView','org/cocos2dx/lib/Cocos2dxWebView','org/cocos2dx/lib/Cocos2dxWebViewHelper'}

def patch_smali(base):
 base=Path(base);receipts=[]
 for cls,parent,names in (('com/square_enix/ffbejpn/Lapis','org/cocos2dx/lib/Cocos2dxActivity',tuple(CALLBACKS)),('org/cocos2dx/lib/Cocos2dxActivity','android/app/Activity',('onCreate','onPause','onResume','onDestroy','onWindowFocusChanged','onActivityResult'))):
  p=base/(cls+'.smali');before=p.read_text(encoding='utf-8');s=before;assert 'gameNativeStarted' not in s
  s=s.replace('# direct methods','# instance fields\n.field private gameNativeStarted:Z\n\n# direct methods',1)
  if cls.endswith('/Lapis'):
   m=re.search(r'\.method static constructor <clinit>\(\)V\n.*?\.end method',s,re.S);assert m and 'Ljava/lang/System;->loadLibrary' in m.group()
   s=s[:m.start()]+'.method static constructor <clinit>()V\n    .registers 0\n    return-void\n.end method'+s[m.end():]
  for name in names:
   regex=r'(\.method[^\n]*\b'+name+r'\([^\n]*\n\s*\.registers \d+\n)';m=re.search(regex,s);assert m,(cls,name)
   params=4 if name in ('onActivityResult','onRequestPermissionsResult') else 2 if name in ('onCreate','onWindowFocusChanged') else 1
   count=int(re.search(r'\.registers (\d+)',m.group())[1])
   if count<=params:
    replacement=m.group().replace('.registers '+str(count),'.registers '+str(params+1));s=s[:m.start()]+replacement+s[m.end():];m=re.search(regex,s)
   args='{'+', '.join('p'+str(i) for i in range(params))+'}'
   gate='invoke-static {}, LO1/GameAssets;->bootReady()Z\n    move-result v0' if name=='onCreate' else 'iget-boolean v0, p0, L'+cls+';->gameNativeStarted:Z'
   prefix='\n    '+gate+'\n    if-nez v0, :game_ready_'+name+'\n    invoke-super '+args+', L'+parent+';->'+name+CALLBACKS[name]+'\n'
   if name=='onCreate' and cls.endswith('/Cocos2dxActivity'):prefix+='    invoke-static {p0}, LO1/GameAssetsBoot;->redirect(Landroid/app/Activity;)V\n'
   prefix+='    return-void\n    :game_ready_'+name+'\n'
   if name=='onCreate':
    if cls.endswith('/Lapis'):prefix+='    const-string v0, "game"\n    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V\n'
    prefix+='    const/4 v0, 0x1\n    iput-boolean v0, p0, L'+cls+';->gameNativeStarted:Z\n'
   s=s[:m.end()]+prefix+s[m.end():]
  p.write_text(s,encoding='utf-8');receipts.append({'class':cls,'changes':'defer native initialization until boot files verified; per-instance lifecycle guards','before':hashlib.sha256(before.encode()).hexdigest(),'after':hashlib.sha256(s.encode()).hexdigest()})
 p=base/'O1/e.smali';before=p.read_text(encoding='utf-8');s=before
 for cls in ('StoryPortTables','SideStoryTables'):
  call='    invoke-static {}, LO1/'+cls+';->prepareIndexes()V';assert call in s;s=s.replace(call,'    # Prepared by ContentDownloader after all required game data is verified.',1)
 p.write_text(s,encoding='utf-8');receipts.append({'class':'O1/e','changes':'remove eager table reads before native download completion'})
 p=base/'com/square_enix/ffbejpn/FridaBootstrap.smali';s=p.read_text(encoding='utf-8');m=re.search(r'\.method public static declared-synchronized bootstrap\(Landroid/content/Context;\)V\n.*?\.end method',s,re.S);assert m
 replacement='.method public static bootstrap(Landroid/content/Context;)V\n    .registers 1\n    invoke-static {p0}, LO1/GameAssets;->runtime(Landroid/content/Context;)V\n    return-void\n.end method';s=s[:m.start()]+replacement+s[m.end():];p.write_text(s,encoding='utf-8');receipts.append({'class':'FridaBootstrap','changes':'retain signed runtime extraction and gadget start; remove legacy synchronous plate network/bulk ZIP download'})
 consumer_paths=set()
 for cls in GAME_CONSUMERS:
  p=base/(cls+'.smali');consumer_paths.add(p);consumer_paths.update(p.parent.glob(p.stem+'$*.smali'))
 for p in sorted(consumer_paths):
  cls=p.relative_to(base).with_suffix('').as_posix()
  if not p.exists():continue
  s=p.read_text(encoding='utf-8');changes=[]
  mappings={'Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;':'LO1/GameAssets;->open(Landroid/content/res/AssetManager;Ljava/lang/String;)Ljava/io/InputStream;','Landroid/content/res/AssetManager;->open(Ljava/lang/String;I)Ljava/io/InputStream;':'LO1/GameAssets;->open(Landroid/content/res/AssetManager;Ljava/lang/String;I)Ljava/io/InputStream;','Landroid/content/res/AssetManager;->openFd(Ljava/lang/String;)Landroid/content/res/AssetFileDescriptor;':'LO1/GameAssets;->openFd(Landroid/content/res/AssetManager;Ljava/lang/String;)Landroid/content/res/AssetFileDescriptor;','Landroid/content/res/AssetManager;->list(Ljava/lang/String;)[Ljava/lang/String;':'LO1/GameAssets;->list(Landroid/content/res/AssetManager;Ljava/lang/String;)[Ljava/lang/String;','Landroid/graphics/Typeface;->createFromAsset(Landroid/content/res/AssetManager;Ljava/lang/String;)Landroid/graphics/Typeface;':'LO1/GameAssets;->typeface(Landroid/content/res/AssetManager;Ljava/lang/String;)Landroid/graphics/Typeface;'}
  for old,new in mappings.items():
   pattern=r'invoke-(virtual|static)(/range)? (\{[^\n]+\}), '+re.escape(old)
   s,n=re.subn(pattern,lambda m:'invoke-static'+(m[2] or '')+' '+m[3]+', '+new,s)
   if n:changes.append({'call':old,'count':n})
  pattern=r'(    invoke-virtual \{([^}\n]+)\}, Landroid/webkit/WebView;->loadUrl\(Ljava/lang/String;\)V)'
  def web(m):
   reg=m[2].split(',')[-1].strip();return '    invoke-static {'+reg+'}, LO1/GameAssets;->webURL(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object '+reg+'\n'+m[1]
  s,n=re.subn(pattern,web,s)
  if n:changes.append({'call':'WebView.loadUrl','count':n})
  pattern=r'(    invoke-virtual/range \{([vp])(\d+) \.\. [vp]\d+\}, Landroid/webkit/WebView;->loadDataWithBaseURL\(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;\)V)'
  def web_base(m):
   reg=m[2]+str(int(m[3])+1);return '    invoke-static {'+reg+'}, LO1/GameAssets;->webURL(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object '+reg+'\n'+m[1]
  s,n=re.subn(pattern,web_base,s)
  if n:changes.append({'call':'WebView.loadDataWithBaseURL','count':n})
  if changes:p.write_text(s,encoding='utf-8');receipts.append({'class':cls,'external_filesystem_consumers':changes})
 return receipts

if __name__=='__main__':
 import sys
 print(json.dumps(patch_smali(sys.argv[1]),indent=2))
