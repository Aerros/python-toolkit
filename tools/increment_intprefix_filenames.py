""" README
Purpose: Add 1 to the number at the front of every file name in one folder.
            1_claims.txt   ->  2_claims.txt
            09_notes.csv   ->  10_notes.csv
Output: Renames the files in place. Returns (renamed, skipped) so the caller can report.
Personal Variables: Find "#!REPLACE" comments to locate.

CRITICAL - the order of renames matters:
    If 1_a.txt and 2_b.txt both exist, renaming 1 -> 2 first would collide with 2_b.txt.
    So we rename the HIGHEST number first and work downward:
            3_c.txt -> 4_c.txt
            2_b.txt -> 3_b.txt
            1_a.txt -> 2_a.txt
    Each target name is freed up just before it is needed. Going the other
    direction would either overwrite a file or fail partway through.

Behavior:
    Only files directly inside FOLDER are touched. Subfolders are ignored.
    Files with no leading number are ignored, not errors.
    Zero padding is preserved: "01_" -> "02_", and "09_" -> "10_" when it has to grow.
    If a target name is already taken by a file we are not renaming, that file is
    skipped and reported rather than overwritten.
    DRY_RUN = True shows what would happen without touching anything.
    Same idea as @WhatIf = 1 in sp_BlitzUpdate: look before you leap.
"""

import re
from pathlib import Path

FOLDER = Path(r"C:\use\your\directory\subfolder")                               #!REPLACE - the folder holding the files
STEP = 1                                                                        #!REPLACE - use -1 to count down instead
DRY_RUN = True                                                                  #!REPLACE - set False once the preview looks right

LEADING_NUMBER = re.compile(r"^(?P<number>\d+)(?P<rest>_.*)$")                   #!REPLACE - drop the _ if names look like "1xxx.y"


def numbered_files(folder: Path) -> list[tuple[int, Path]]:                     # returns pairs so we can sort by the number
    """Return (number, path) for every file in folder whose name starts with digits."""
    found = []
    for item in folder.iterdir():                                               # FROM - one level only, no recursion
        if not item.is_file():                                                  # WHERE - skip subfolders
            continue
        match = LEADING_NUMBER.match(item.name)                                 # .match anchors at the start of the name
        if not match:                                                           # WHERE - skip names with no leading number
            continue
        found.append((int(match.group("number")), item))                        # int() so 10 sorts after 9, not before 2
    return found


def bumped_name(path: Path) -> str:
    """Return the file name with its leading number moved by STEP."""
    match = LEADING_NUMBER.match(path.name)                                     # safe: only called on names that already matched
    digits = match.group("number")                                              # the text, e.g. "09" - keeps the original width
    new_number = int(digits) + STEP                                             # the value, e.g. 9 + 1 = 10
    return str(new_number).zfill(len(digits)) + match.group("rest")             # zfill pads back to the original width


def increment_names(folder: Path) -> tuple[int, int]:
    """Rename every numbered file in folder. Returns (renamed, skipped)."""
    if not folder.exists():                                                     # guard: fail here with a clear message
        raise RuntimeError(f"Folder does not exist: {folder}")                  # rather than 20 lines later with a vague one

    renamed = 0
    skipped = 0

    for number, path in sorted(numbered_files(folder), reverse=STEP > 0):       # highest first when adding, lowest first when subtracting
        target = path.with_name(bumped_name(path))                              # same folder, new name

        if target.exists():                                                     # something is already sitting there
            print(f"SKIP      {path.name} -> {target.name} (target exists)")
            skipped += 1
            continue

        if DRY_RUN:
            print(f"WOULD BE  {path.name} -> {target.name}")
        else:
            path.rename(target)                                                 # .rename refuses to clobber on Windows; .replace would overwrite
            print(f"RENAMED   {path.name} -> {target.name}")
        renamed += 1

    return renamed, skipped


if __name__ == "__main__":                                                      # only runs when the file is run directly
    done, left = increment_names(FOLDER)
    print(f"\n{done} file(s) {'previewed' if DRY_RUN else 'renamed'}, {left} skipped.")
    if DRY_RUN:
        print("DRY_RUN is True - nothing was changed. Set it to False to apply.")