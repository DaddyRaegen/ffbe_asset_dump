"""Normalize wording in owned206 documents, without changing release data."""
from pathlib import Path
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
bases=[Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\event_cleanup_v206'),Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-10-04-event-cleanup-v206')]
replacements={'APK206':'APK 206','exactAPK':'exact APK','ZFold8':'Z Fold 8','Android17':'Android 17','Image2.5':'Image 2.5','move20':'move 20','exclude41':'exclude 41','replace12':'replace 12','All1,760':'All 1,760','requested Image2.5':'requested Image 2.5','RevivalPart1':'Revival Part 1','RevivalPart2':'Revival Part 2','OriginalGenesis7032':'Original Genesis 7032','originalGenesis7032':'original Genesis 7032','Parts1/2':'Parts 1/2','RevivalParts1/2':'Revival Parts 1/2','the20':'the 20','StoryEvents':'Story Events','EventBattles':'Event Battles','ArchivedEventBattles':'Archived Event Battles','ANewYear\'sGreeting':'A New Year\'s Greeting','UnitIntroQuest':'Unit Intro Quest','PartyTest':'Party Test','JPMemories':'JP Memories','mainstory':'main story','known available movie and originalcontent':'known available movie and original content','exactbuild/SHA':'exact build/SHA','device/Androidversion':'device/Android version','native640×240':'native 640×240','Literal Patch5/205':'Literal Patch 5/205','native ELF16KB':'native ELF 16 KB','historical203/204':'historical 203/204','a206 coverage':'a 206 coverage','for206':'for 206'}
paths=[ROOT/'audit/prepare_handoff_skeleton.py',ROOT/'audit/copy_frozen_handoff.py']
for base in bases:paths += [base/'README.md',*sorted((base/'documents').glob('*.md'))]
for path in paths:
 text=path.read_text(encoding='utf-8')
 for before,after in replacements.items():text=text.replace(before,after)
 path.write_text(text,encoding='utf-8')
print('Polished owned206 documentation wording; historical releases and runtime untouched.')
