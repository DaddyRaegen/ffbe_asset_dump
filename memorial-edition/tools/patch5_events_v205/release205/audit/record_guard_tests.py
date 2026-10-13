"""Run and pin the independent minimal-release mutation suite."""
from pathlib import Path
import datetime,io,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'guard'))
import patch5_event_guard as g
import test_patch5_event_guard
stream=io.StringIO()
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_patch5_event_guard))
(ROOT/'audit/GUARD_REGRESSION_TESTS.txt').write_text(stream.getvalue(),encoding='utf-8')
report={'schema':'ffbe-patch5-event-only-guard-regression-v1','passed':result.wasSuccessful(),
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'source_pins':{p.name:g.file_sha(p) for p in (ROOT/'guard/patch5_event_guard.py',ROOT/'guard/test_patch5_event_guard.py')},
        'fixtures':{'production_apk_sha256':g.BASELINE_SHA,'real_patched_reference':'audit/original-downloader/patched-decoded-smali'},
        'network_checks':False,'device_actions':False,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(ROOT/'audit/GUARD_REGRESSION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
raise SystemExit(0 if result.wasSuccessful() else 1)
