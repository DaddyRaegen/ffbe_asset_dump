from pathlib import Path
import datetime, hashlib, io, json, unittest
import download_spacing_guard as guard

buffer = io.StringIO()
suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), 'test_download_spacing_guard.py')
result = unittest.TextTestRunner(stream=buffer, verbosity=2).run(suite)
log = guard.ROOT/'audit/GUARD_REGRESSION_TESTS.txt'
log.write_text(buffer.getvalue(), encoding='utf-8')
report = {'schema': 'ffbe-download-spacing-guard-regression-v1', 'passed': result.wasSuccessful(),
    'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
    'baseline_apk_sha256': guard.BASELINE_APK_SHA, 'spacing_plan_sha256': guard.file_sha(guard.ROOT/'audit/DOWNLOAD_SPACING_PLAN.json'),
    'sources': {p.name: guard.file_sha(p) for p in [Path(guard.__file__), Path(__file__),
        Path(__file__).with_name('test_download_spacing_guard.py')]},
    'transcript': str(log), 'transcript_sha256': guard.file_sha(log)}
path = guard.ROOT/'audit/GUARD_REGRESSION.json'
path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))
raise SystemExit(0 if result.wasSuccessful() else 1)
