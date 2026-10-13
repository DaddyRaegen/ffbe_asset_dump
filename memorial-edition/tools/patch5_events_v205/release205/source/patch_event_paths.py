"""Extend literal Patch 5 only for pinned JP/GL scene CPK paths.

The source classes must be disassembled from the pinned production Patch 5 APK
with the retained baksmali.jar default options. No downloader, cache, resume,
startup, callback, movie or UI method is replaced. CRLF is accepted on input;
all hash pins refer to the otherwise exact UTF-8 text with LF line endings.
"""
from pathlib import Path
import hashlib

PATCH5_APK_SHA256 = '534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
ORIGINAL_CLASS_PINS = {
    'O1/ExtraContent$Entry.smali': '259c30849a729880005884265eac9f2f0be5da39c7e149010ce7662d415aa5f9',
    'O1/SideStoryTables.smali': '5977ecd452a81b531e4c2a69df689c48caa2645509c69fd771fa38d29252c697',
}
ORIGINAL_EXTRA_PATH_PATTERN = '(side_stories|story_ports|battle|encyclopedia)/[A-Za-z0-9_.-]+'
ORIGINAL_SIDE_PATH_PATTERN = '[A-Za-z0-9_.-]+'
SCENE_PATH_PATTERN = 'r2_scene_(jp|gl)/[a-f0-9]{16}/[A-Za-z0-9_.-]+[.]cpk'
EXTRA_PATH_PATTERN = '(?:' + ORIGINAL_EXTRA_PATH_PATTERN + '|side_stories/' + SCENE_PATH_PATTERN + ')'
SIDE_PATH_PATTERN = '(?:' + ORIGINAL_SIDE_PATH_PATTERN + '|' + SCENE_PATH_PATTERN + ')'

ORIGINAL_DIRECTORY_BLOCK = '''    :try_start_eb
    invoke-virtual {v6}, Ljava/io/File;->isDirectory()Z

    move-result v8

    if-nez v8, :cond_f9

    invoke-virtual {v6}, Ljava/io/File;->mkdirs()Z
'''
DIRECTORY_BLOCK = '''    :try_start_eb
    invoke-virtual {v7}, Ljava/io/File;->getParentFile()Ljava/io/File;

    move-result-object v9

    invoke-virtual {v9}, Ljava/io/File;->isDirectory()Z

    move-result v8

    if-nez v8, :cond_f9

    invoke-virtual {v9}, Ljava/io/File;->mkdirs()Z
'''

def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _replace(text, before, after, count):
    if text.count(before) != count:
        raise ValueError(f'Expected {count} exact original occurrences, found {text.count(before)}')
    return text.replace(before, after)

def patch_text(relative_path, original):
    """Return patched text and a reviewable exact-edit receipt; never write files."""
    relative_path = str(relative_path).replace('\\', '/')
    text = original.replace('\r\n', '\n')
    expected = ORIGINAL_CLASS_PINS.get(relative_path)
    if expected is None or _sha(text) != expected:
        raise ValueError(f'Class does not match literal Patch 5: {relative_path}')
    edits = []
    if relative_path == 'O1/ExtraContent$Entry.smali':
        text = _replace(text, '"' + ORIGINAL_EXTRA_PATH_PATTERN + '"', '"' + EXTRA_PATH_PATTERN + '"', 1)
        edits.append({'method': '<init>([Ljava/lang/String;)V', 'before': ORIGINAL_EXTRA_PATH_PATTERN,
                      'after': EXTRA_PATH_PATTERN, 'occurrences': 1})
    else:
        text = _replace(text, '"' + ORIGINAL_SIDE_PATH_PATTERN + '"', '"' + SIDE_PATH_PATTERN + '"', 2)
        edits.append({'methods': ['choose(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;',
                                  'load(Ljava/lang/Object;)V'], 'before': ORIGINAL_SIDE_PATH_PATTERN,
                      'after': SIDE_PATH_PATTERN, 'occurrences': 2})
        text = _replace(text, ORIGINAL_DIRECTORY_BLOCK, DIRECTORY_BLOCK, 1)
        edits.append({'method': 'choose(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;',
                      'before': ORIGINAL_DIRECTORY_BLOCK, 'after': DIRECTORY_BLOCK, 'occurrences': 1,
                      'purpose': 'Create parent directories for the target nested scene name; original temp/cache paths unchanged.'})
    return text, {'path': relative_path, 'original_sha256': _sha(original),
                  'original_normalized_sha256': expected,
                  'patched_normalized_sha256': _sha(text), 'edits': edits}

def patch(smali_root):
    """Apply both classes only after validating both original class seals."""
    smali_root = Path(smali_root)
    staged = []
    for relative_path in ORIGINAL_CLASS_PINS:
        path = smali_root / relative_path
        original = path.read_bytes().decode('utf-8')
        text, receipt = patch_text(relative_path, original)
        staged.append((path, text, receipt))
    for path, text, _ in staged:
        path.write_bytes(text.encode('utf-8'))
    return [receipt for _, _, receipt in staged]

def patch_smali(base_smali_dir):
    """Builder API: edit only the two sealed classes inside the provided tree."""
    receipts = patch(base_smali_dir)
    return {
        'schema': 'ffbe-patch5-minimal-event-paths-smali-v1',
        'source_apk_sha256': PATCH5_APK_SHA256,
        'classes': [{'path': row['path'], 'before_sha256': row['original_sha256'],
                     'before_normalized_sha256': row['original_normalized_sha256'],
                     'after_sha256': row['patched_normalized_sha256'], 'changes': row['edits']}
                    for row in receipts],
        'changed_class_count': 2,
        'changed_methods': ['O1/ExtraContent$Entry.<init>', 'O1/SideStoryTables.load',
                            'O1/SideStoryTables.choose'],
        'all_other_smali_classes_preserved': True,
        'ContentDownloader_CdnDownloader_e_ResumableTransfer_unchanged': True,
        'startup_lifecycle_callbacks_movie_UI_unchanged': True,
        'native_libraries_unchanged': True,
        'compiled_java_overlay_used': False,
        'runtime_verified': False,
    }
