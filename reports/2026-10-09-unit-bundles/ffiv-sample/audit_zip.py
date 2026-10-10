"""Read-only audit of the supplied icon ZIP; extracted previews are contained here."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = None
REPO = Path(__file__).resolve().parents[3]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    global ROOT, SOURCE, REPO
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, required=True, dest='source')
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--output', type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT, SOURCE, REPO = args.output.resolve(), args.source.resolve(), args.repo.resolve()
    ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    errors = []
    documents = {}
    with zipfile.ZipFile(SOURCE) as archive:
        crc_error = archive.testzip()
        for member in archive.infolist():
            if member.is_dir():
                continue
            raw = archive.read(member)
            if not member.filename.lower().endswith(".png"):
                documents[member.filename] = raw.decode("utf-8")
                continue
            path = (ROOT / "images" / member.filename).resolve()
            if not path.is_relative_to(ROOT):
                raise ValueError(f"Unsafe archive path: {member.filename}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            try:
                with Image.open(io.BytesIO(raw)) as probe:
                    probe.verify()
                with Image.open(io.BytesIO(raw)) as source:
                    source.load()
                    image = source.convert("RGBA")
                    alpha = image.getchannel("A")
                    hist = alpha.histogram()
                    unit_id = re.search(r"_(\d+)\.png$", member.filename).group(1)
                    rows.append({
                        "path": member.filename,
                        "filename": path.name,
                        "group": "large" if "ICON-Large/" in member.filename else "ability",
                        "id": unit_id,
                        "width": source.width,
                        "height": source.height,
                        "mode": source.mode,
                        "format": source.format,
                        "bytes": len(raw),
                        "sha256": digest(raw),
                        "rgba_sha256": digest(image.tobytes()),
                        "transparent_pixels": hist[0],
                        "partial_alpha_pixels": sum(hist[1:255]),
                        "opaque_pixels": hist[255],
                        "alpha_bbox": list(alpha.getbbox()),
                        "rgba_colors": len(image.getcolors(source.width * source.height)),
                        "metadata_keys": sorted(source.info),
                    })
            except Exception as exc:
                errors.append({"path": member.filename, "error": str(exc)})
    groups = {}
    for group in ("large", "ability"):
        chosen = [row for row in rows if row["group"] == group]
        by_pixels = collections.defaultdict(list)
        for row in chosen:
            by_pixels[row["rgba_sha256"]].append(row["filename"])
        groups[group] = {
            "images": len(chosen),
            "dimensions": dict(collections.Counter(f'{r["width"]}x{r["height"]}' for r in chosen)),
            "modes": dict(collections.Counter(r["mode"] for r in chosen)),
            "byte_range": [min(r["bytes"] for r in chosen), max(r["bytes"] for r in chosen)],
            "unique_file_hashes": len({r["sha256"] for r in chosen}),
            "unique_pixel_images": len(by_pixels),
            "duplicates": [names for names in by_pixels.values() if len(names) > 1],
            "transparent_pixel_range": [min(r["transparent_pixels"] for r in chosen), max(r["transparent_pixels"] for r in chosen)],
            "partial_alpha_pixel_range": [min(r["partial_alpha_pixels"] for r in chosen), max(r["partial_alpha_pixels"] for r in chosen)],
        }
    ids = {group: {r["id"] for r in rows if r["group"] == group} for group in groups}
    list_names = {line.strip() + ".png" for line in documents["Iconlist_04_FFIV.md"].splitlines() if line.startswith("ICON")}
    actual_names = {r["filename"] for r in rows}
    master = json.loads((REPO / "catalog/unit_master.json").read_text(encoding="utf-8"))
    units = master["units"]
    if isinstance(units, list):
        master_ids = {str(u.get("original_id", u.get("master_id", ""))) for u in units}
    else:
        master_ids = set(units)
    summary = {
        "source": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": digest(SOURCE.read_bytes()),
        "crc_error": crc_error,
        "image_count": len(rows),
        "image_decode_errors": errors,
        "document_names": list(documents),
        "groups": groups,
        "large_only_ids": sorted(ids["large"] - ids["ability"]),
        "ability_only_ids": sorted(ids["ability"] - ids["large"]),
        "id_length_outliers": [{"path": r["path"], "id": r["id"]} for r in rows if len(r["id"]) != 9],
        "listed_but_absent": sorted(list_names - actual_names),
        "present_but_unlisted": sorted(actual_names - list_names),
        "ids_absent_from_master": sorted((ids["large"] | ids["ability"]) - master_ids),
    }
    (ROOT / "audit.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (ROOT / "image-inventory.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "image-inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    compact = {k: v for k, v in summary.items() if k != "groups"}
    compact["groups"] = {g: {k: v for k, v in values.items() if k != "duplicates"} for g, values in groups.items()}
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()
