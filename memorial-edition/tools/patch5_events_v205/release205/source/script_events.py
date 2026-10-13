"""Add only explicit event party markers and the beta release counter/routes."""
import hashlib,json,re
BASELINE='31a87e1c3deff7f22d692f5a35d476db76b3d0f6639eb0c487fda9b91fb02b44'
UPDATER='https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/patch_version.json'
DOWNLOAD='https://ffbe.luminest.io/downloads/beta/'
def patch(original,party_book_ids,version=205):
 assert hashlib.sha256(original).hexdigest()==BASELINE
 text=original.decode('utf-8');marker='const SIDE_STORY_PARTIES = '
 assert text.count(marker)==1
 start=text.index(marker)+len(marker);parties,length=json.JSONDecoder().raw_decode(text[start:])
 assert len(parties['books'])==85 and len(parties['entries'])==2177
 added=[]
 for book in party_book_ids:
  key=str(book)
  if key not in parties['books']:parties['books'][key]=[];added.append(int(book))
 text=text[:start]+json.dumps(parties,separators=(',',':'),ensure_ascii=False)+text[start+length:]
 changes={
  'const PATCH_VERSION = 5;':f'const PATCH_VERSION = {version};',
  'https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/patch_version.json':UPDATER,
  'const DOWNLOAD_URL   = "https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest";':f'const DOWNLOAD_URL   = "{DOWNLOAD}";',
 }
 for before,after in changes.items():assert text.count(before)==1;text=text.replace(before,after)
 # No native/root adapter, new classifier, movie edit, hook or other feature.
 return text.encode('utf-8'),{'added_party_book_markers':added,'existing_party_books':85,'existing_entry_parties':2177,'existing_party_entries_unchanged':True,'all_non_event_hooks_unchanged':True,'version':version}
