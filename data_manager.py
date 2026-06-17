from __future__ import annotations

import argparse
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

import yaml


# ============================================================
# Configuration
# ============================================================

EXPERIMENT_CONFIG = {
    "2choice": {"dpf": 7, "required_fields": ["contrast", "stimSides"]},
    "openField": {"dpf": 8, "required_fields": []},
    "mirrortest": {"dpf": 21, "required_fields": ["mirrorPos"]},
    "socialpreference": {"dpf": 28, "required_fields": ["stimSides"]},
}

ALLOWED_CONTRASTS = {
    "1vs2", "1vs3", "1vs4", "2vs4", "2vs6", "2vs6sf"
}

ALLOWED_MIRROR_POS = {"top", "bottom"}

ALLOWED_APPARATUS = {"box", "well"}

APPARATUS_REAL_SIZE = {
    "box": [80, 54],
    "well": 18.0,
}

DESCRIPTION_TEXT = {
    "apparatusCoords": "for box [top left xy, bottom right xy], for well [[cx, cy], r]",
    "apparatusRealSize": "in mm. for box width and height. for well radius",
    "apparatusType": "apparatus type. can be box or well",
    "date": "trial date in YYYYmmdd",
    "dpf": "days post fertilization",
    "expType": "the experiment type",
    "subj": "the subject ID",
    "trialn": "the trial number",
}

FPS = 30


# ============================================================
# Filename parsing
# ============================================================

FILENAME_RE = re.compile(
    r"^sub-(f\d{4})_"
    r"expType-([A-Za-z0-9]+)_"
    r"trialn-(\d+)_"
    r"date-(\d{8})_recording\.mp4$"
)


def parse_filename(name: str) -> dict:
    m = FILENAME_RE.match(name)
    if not m:
        raise ValueError(f"Invalid filename: {name}")

    subj, exp, trial, date = m.groups()

    if exp not in EXPERIMENT_CONFIG:
        raise ValueError(f"Unknown expType: {exp}")

    datetime.strptime(date, "%Y%m%d")

    return {
        "subj": subj,
        "expType": exp,
        "trialn": int(trial),
        "date": date,
    }


def propose_filename_fix(name: str) -> str | None:
    fixed = name

    fixed = re.sub(r"_+", "_", fixed)

    if fixed.endswith(".mp4") and not fixed.endswith("_recording.mp4"):
        base = fixed[:-4]
        if "_date-" in base:
            fixed = base + "_recording.mp4"

    return None if fixed == name else fixed


# ============================================================
# Defaults
# ============================================================

def prompt_default(msg: str, default=None) -> str:
    if default is not None:
        v = input(f"{msg} [{default}]: ").strip()
        return str(default if v == "" else v)
    return input(f"{msg}: ").strip()


# ============================================================
# Interactive prompts
# ============================================================

def ask_apparatus(defaults: dict) -> str:
    while True:
        v = prompt_default("apparatusType (box/well)", defaults.get("apparatusType"))
        if v in ALLOWED_APPARATUS:
            defaults["apparatusType"] = v
            return v
        print("invalid apparatusType")


def ask_contrast(defaults: dict) -> str:
    while True:
        v = prompt_default("contrast", defaults.get("contrast"))
        if v in ALLOWED_CONTRASTS:
            defaults["contrast"] = v
            return v
        print("invalid contrast")


def ask_mirror(defaults: dict) -> str:
    while True:
        v = prompt_default("mirrorPos", defaults.get("mirrorPos"))
        if v in ALLOWED_MIRROR_POS:
            defaults["mirrorPos"] = v
            return v
        print("invalid mirrorPos")


def ask_stim_sides(defaults: dict) -> list[int]:
    prev = defaults.get("stimSides")

    while True:
        try:
            l = int(prompt_default("Left stimulus", prev[0] if prev else None))
            r = int(prompt_default("Right stimulus", prev[1] if prev else None))
            defaults["stimSides"] = [l, r]
            return [l, r]
        except Exception:
            print("stimSides must be two integers")


# ============================================================
# Metadata
# ============================================================

def build_metadata(meta: dict, defaults: dict) -> dict:
    out = dict(meta)

    exp = out["expType"]

    out["dpf"] = EXPERIMENT_CONFIG[exp]["dpf"]
    out["fps"] = FPS

    atype = ask_apparatus(defaults)
    out["apparatusType"] = atype
    out["apparatusRealSize"] = APPARATUS_REAL_SIZE[atype]

    if exp == "2choice":
        out["contrast"] = ask_contrast(defaults)
        out["stimSides"] = ask_stim_sides(defaults)

    elif exp == "mirrortest":
        out["mirrorPos"] = ask_mirror(defaults)

    elif exp in ["socialpreference"]:
        out["stimSides"] = ask_stim_sides(defaults)

    return out


# ============================================================
# YAML serialization
# ============================================================

def to_yaml(data: dict) -> str:
    lines = []

    lines.append("apparatusCoords:")

    val = data["apparatusRealSize"]
    if isinstance(val, list):
        lines.append("apparatusRealSize:")
        for x in val:
            lines.append(f"  - {x}")
    else:
        lines.append(f"apparatusRealSize: {val}")

    lines.append(f"apparatusType: {data['apparatusType']}")
    lines.append(f'date: "{data["date"]}"')

    lines.append("description:")
    for k, v in DESCRIPTION_TEXT.items():
        lines.append(f"  {k}: {v}")

    lines.append(f"dpf: {data['dpf']}")
    lines.append(f"expType: {data['expType']}")
    lines.append(f"fps: {data['fps']}")
    lines.append(f"subj: {data['subj']}")
    lines.append(f"trialn: {data['trialn']}")

    if "contrast" in data:
        lines.append(f'contrast: "{data["contrast"]}"')

    if "mirrorPos" in data:
        lines.append(f"mirrorPos: {data['mirrorPos']}")

    if "stimSides" in data:
        lines.append("stimSides:")
        for x in data["stimSides"]:
            lines.append(f"  - {x}")

    return "\n".join(lines) + "\n"


def write_yaml(path: Path, data: dict):
    if path.exists():
        ans = input(f"{path.name} exists. overwrite? [y/N]: ").strip().lower()
        if ans != "y":
            logging.info(f"skip yaml {path}")
            return False

    text = to_yaml(data)
    yaml.safe_load(text)

    path.write_text(text)
    logging.info(f"write yaml {path}")
    return True


# ============================================================
# Validation
# ============================================================

def validate_yaml(meta: dict, video_meta: dict) -> list[str]:
    err = []

    for f in ["subj", "expType", "trialn", "date"]:
        if meta.get(f) != video_meta[f]:
            err.append(f"{f} mismatch")

    if meta.get("fps") != 30:
        err.append("fps must be 30")

    if not isinstance(meta.get("trialn"), int):
        err.append("trialn must be int")

    return err


# ============================================================
# File handling
# ============================================================

def metadata_path(video: Path) -> Path:
    return video.with_name(
        video.name.replace("_recording.mp4", "_metadata.yml")
    )


def process_video(video: Path, dest: Path, defaults: dict):
    try:
        meta = parse_filename(video.name)
    except Exception as e:
        print(f"invalid filename {video.name}: {e}")
        return

    corrected = propose_filename_fix(video.name)

    if corrected:
        print(video.name, "->", corrected)
        if input("apply? [y/N]: ").strip().lower() == "y":
            new_path = video.with_name(corrected)
            video.rename(new_path)
            video = new_path
            meta = parse_filename(video.name)

    dest_video = dest / video.name
    dest_yaml = metadata_path(dest_video)

    if dest_video.exists():
        print(f"skip existing video {dest_video.name}")
        return

    shutil.copy2(video, dest_video)

    print("\n" + "=" * 50)
    print("Processing recording:")
    print(video.name)
    print("=" * 50 + "\n")

    meta_full = build_metadata(meta, defaults)

    if dest_yaml.exists():
        print(f"metadata exists: {dest_yaml.name}")
        existing = yaml.safe_load(dest_yaml.read_text())
        errs = validate_yaml(existing, meta)
        if errs:
            print("validation errors:")
            for e in errs:
                print("-", e)
        return

    write_yaml(dest_yaml, meta_full)


# ============================================================
# Main
# ============================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--destination", required=True)
    args = ap.parse_args()

    src = Path(args.source)
    dst = Path(args.destination)

    if not src.exists() or not dst.exists():
        raise FileNotFoundError("source or destination missing")

    logging.basicConfig(
        filename=dst / "processing.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )

    defaults = {}

    for f in src.glob("*.mp4"):
        process_video(f, dst, defaults)


if __name__ == "__main__":
    main()