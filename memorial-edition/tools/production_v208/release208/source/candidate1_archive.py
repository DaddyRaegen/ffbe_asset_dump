"""Replace active outputs only after proving their immutable candidate archive."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT.parent/'v208-production-candidate1'
ARCHIVES=[ROOT.parent/'v208-production-candidate2',ARCHIVE]

def put(path, data):
    path=Path(path).resolve()
    relative=path.relative_to(ROOT.resolve())
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        previous=path.read_bytes()
        if previous==data:return
        assert any((archive/relative).is_file() and (archive/relative).read_bytes()==previous for archive in ARCHIVES), 'Active bytes differ from immutable candidate archives: '+str(path)
    path.write_bytes(data)
