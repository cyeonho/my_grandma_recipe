from __future__ import annotations
import argparse
import csv
from pathlib import Path

COLS = ["OBJNAME","OBJTYPE","GROUP1","GROUP2","EXPTIME",
        "RECIPE","OBSIDS","FRAMETYPES"]

def split_ab_pairs(row: list[str]) -> list[list[str]]:
    """
    Given one STELLAR_AB line, return a list with one new row
    per successive (A B) or (B A) pair.  Any incomplete tail
    (odd number of frames) is discarded.
    """
    obsids      = row[6].split()         # OBSIDS column
    frametypes  = row[7].split()         # FRAMETYPES column
    out         = []

    for i in range(0, min(len(obsids), len(frametypes)), 2):
        if i + 1 >= len(obsids):          # orphan at end
            break
        pair_ids   = obsids[i:i+2]
        pair_types = frametypes[i:i+2]
        pattern    = " ".join(pair_types)

        if pattern not in ("A B", "B A"):  # ignore strange cases
            continue

        new_row = row.copy()
        new_row[2] = pair_ids[0]              # GROUP1 ¡æ first OBSID
        new_row[6] = " ".join(pair_ids)       # OBSIDS   (two only)
        new_row[7] = pattern                  # FRAMETYPES as "A B"
        out.append(new_row)

    return out


def process_one_file(path: Path) -> None:
    out_rows: list[list[str]] = []

    with path.open(newline="") as fh:
        for raw in csv.reader((ln for ln in fh if not ln.lstrip().startswith("#"))):
            if len(raw) < 8:          # skip malformed line
                continue
            # pad short rows so raw[i] works safely
            raw += [""] * (8 - len(raw))

            if raw[1].strip() != "TAR":
                continue
            out_rows.extend(split_ab_pairs(raw))

    if not out_rows:
        print(f"[{path.name}] nothing to write (no TAR AB/BA pairs).")
        return

    out_file = path.parent / f"{path.stem}_fixed"
    with out_file.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(out_rows)

    print(f"[{path.name}] wrote {len(out_rows):3d} AB/BA rows to {out_file.name}")

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Break OBSIDS list into successive A B / B A pairs "
                    "for all *.recipes.tmp files.")
    ap.add_argument("-f", "--files", nargs="+", required=True,
                    help="input recipe file(s)")
    args = ap.parse_args()

    for fn in args.files:
        process_one_file(Path(fn).expanduser())

if __name__ == "__main__":
    main()
