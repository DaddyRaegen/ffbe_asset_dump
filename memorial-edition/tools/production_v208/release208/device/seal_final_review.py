"""Seal the root's completed, bounded final-APK observations; no device actions."""
from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DEVICE = ROOT / 'device'
EXPECTED = '9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4'
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
def write(path, value): path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

build = read(ROOT/'staged_build/PRODUCTION_APK_BUILD.json')
signed = read(ROOT/'staged_build/SIGNED_PRODUCTION_QUALIFICATION.json')
stage = read(ROOT/'publication/apk-stage-receipt.json')
assets = read(ROOT/'publication/asset-stage-receipt.json')
assert build['sha256'] == signed['apk_sha256'] == stage['sha256'] == EXPECTED
assert build['bytes'] == signed['apk_bytes'] == stage['bytes'] == 145206221
assert signed['passed'] and stage['success'] and assets['success']
assert pin(Path(build['apk']))['sha256'] == EXPECTED
installed = (DEVICE/'prod208-installed-apk-sha256.txt').read_text(encoding='utf-8-sig')
assert installed.split()[0] == EXPECTED
version = (DEVICE/'prod208-package-version.txt').read_text(encoding='utf-8-sig')
assert 'versionCode=208' in version and 'versionName=11.1.1' in version
logs = ['prod208-scoped-runtime.log', 'prod208-cached-runtime.log']
for name in logs:
    text = (DEVICE/name).read_text(encoding='utf-8-sig')
    assert 'FATAL EXCEPTION' not in text and 'Fatal signal' not in text
screens = {
    'startup_title': 'prod208-title.png',
    'new_data_prompt': 'prod208-download-check.png',
    'download_progress': 'prod208-download-progress.png',
    'home_after_download': 'prod208-home.png',
    'event_battles_top': 'prod208-event-top-final.png',
    'protected_DV_and_legitimate_Zanarkand': 'prod208-event-wide-check.png',
    'three_centered_genuine_event_canvases': 'prod208-native-canvases.png',
    'event_fallback_boundary': 'prod208-fallback-boundary.png',
    'JP_Memories_top': 'prod208-jp-top-ready.png',
    'JP_centered_genuine_canvases': 'prod208-jp-native-canvases.png',
    'JP_fallback_boundary_and_protected_DV': 'prod208-jp-fallback.png',
    'Shield_Baton_Canvas_Mirror_sample': 'prod208-named-story-covers.png',
    'Genesis_and_Shield_sample': 'prod208-genesis-shield.png',
    'Revival_parts_last': 'prod208-story-bottom.png',
    'cached_restart_title': 'prod208-cached-title.png',
    'cached_restart_home': 'prod208-cached-home-ready.png',
}
proofs = {label: pin(DEVICE/name) for label, name in screens.items()}
for proof in proofs.values():
    assert Path(proof['path']).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
report = {
    'schema': 'ffbe-production208-bluestacks-review-v1',
    'passed': True, 'candidate_revision': 3, 'versionCode': 208,
    'versionName': build['versionName'], 'package': build['package'],
    'apk_sha256': EXPECTED, 'apk_bytes': build['bytes'],
    'signer_sha256': build['signer_sha256'],
    'test_environment': {'application': 'BlueStacks', 'instance': 'Pie64',
                         'Android_version': 9, 'serial': 'emulator-5554'},
    'installed_apk_matches_final_signed_artifact': True,
    'public_installed_apk_proof': pin(DEVICE/'prod208-installed-apk-sha256.txt'),
    'installed_version_proof': pin(DEVICE/'prod208-package-version.txt'),
    'signed_qualification': pin(ROOT/'staged_build/SIGNED_PRODUCTION_QUALIFICATION.json'),
    'data_publication': pin(ROOT/'publication/asset-stage-receipt.json'),
    'native_download': {'prompt': '47.664MB', 'accepted': True,
        'progress_observed': '36.925MB/47.664MB,77%',
        'completed_and_reached_home': True,
        'completion_basis': 'Changed banner artwork rendered after download and home screen reached.',
        'no_100_percent_frame_captured': True,
        'compact_progress_spacing_confirmed': True,
        'final_catalog_sha256': signed['content_catalog_sha256'],
        'GitHub_immutable_data_release': assets['release_tag']},
    'menus_checked': ['Story Events', 'Event Battles', 'JP Memories'],
    'rendered_checks': [
        'Final event top has illustrated events; three old title placeholders appear at fallback boundary.',
        '600x120 genuine event and JP artwork appears centered without artwork scaling or cropping.',
        'Shield Maiden, Baton, Canvas and Mirror covers have padding and no adjacent-row overlap.',
        'Genesis story cover and both Revival parts display; Revival parts are final rows.',
        'Event and JP fallback title cards fit and follow the genuine artwork prefix.',
        'Protected Dark Visions repeated artwork and its distinct presentation remain.',
        'The legitimate Event Battles Zanarkand cover still displays.'
    ],
    'cached_restart': {'force_stop_and_relaunch': True, 'reached_home': True,
                       'new_download_prompt_seen': False, 'profile': 'Rain, Rank1'},
    'scoped_application_logs': [pin(DEVICE/name) for name in logs],
    'fatal_markers_observed': False,
    'screenshots': proofs,
    'app_data_cleared': False, 'app_uninstalled': False,
    'emulator_test_profile_preserved': True,
    'save_migration_verified': False, 'physical_phone_test': 'pending',
    'limits': ['The emulator profile was created during this qualification sequence.',
              'Physical ZFold8/Android17 startup and an existing real save were not tested.',
              'Banner inventory qualification covers all903 bindings; rendered review is representative.',
              'Every archived battle, movie and server-dependent mechanic was not exercised.'],
    'known_issues': ['Overdrive skills crash the game.', 'dark visions crash the game'],
    'completed_at': datetime.now(timezone.utc).isoformat()
}
write(DEVICE/'BLUESTACKS_V208_REVIEW.json', report)
checkpoint = {
    'schema': 'ffbe-production208-phone-test-checkpoint-v1',
    'versionCode': 208, 'candidate_revision': 3,
    'apk_url': stage['url'], 'apk_sha256': EXPECTED, 'apk_bytes': build['bytes'],
    'physical_phone_test': 'pending', 'save_migration_verified': False,
    'target_device': 'ZFold8', 'target_Android_version': 17,
    'BlueStacks_passed': True,
    'BlueStacks_report': pin(DEVICE/'BLUESTACKS_V208_REVIEW.json'),
    'phone_checklist': pin(ROOT/'publication/site/phone-test-checklist.txt'),
    'phone_checklist_url': stage['url'].rsplit('/', 1)[0]+'/phone-test-checklist.txt',
    'instructions': 'Install over the existing English edition, preserving app data and saves; follow the exact-build checklist.',
    'known_issues': report['known_issues']
}
write(ROOT/'PHONE_TEST_CHECKPOINT.json', checkpoint)
print(json.dumps({'passed': True, 'apk_sha256': EXPECTED, 'apk_bytes': build['bytes'],
                  'review': pin(DEVICE/'BLUESTACKS_V208_REVIEW.json'),
                  'physical_phone_test': 'pending'}))
