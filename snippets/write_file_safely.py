""" README
Purpose: Write a file so it is either complete or absent - never half-written. gunzip_file() is the worked example.
Output: atomic_write() gives you a file handle inside a with-block; gunzip_file() returns the path of the unzipped file.
Personal Variables: None.
Implementation:
    Paste this block into your script.
    Any file you produce:
        with atomic_write(OUTPUT_DIR / "claims.txt") as f:
            f.write(data)
    Decompress every .gz in a folder:
        for gz in sorted(INPUT_DIR.glob("*.gz")):
            gunzip_file(gz)
How it works (the whole idea):
    1. Write to  claims.txt.partial
    2. Only after the last byte is written, RENAME it to claims.txt
    A rename within one folder is all-or-nothing, so the next step in the pipeline (or a SQL import)
    can never pick up a truncated claims.txt from a crash, a full disk, or a dropped network share.
Behavior:
    On any error the .partial file is deleted and the error is re-raised.
    An existing file at the target is replaced only on success.
    gunzip_file deletes the .gz only after the unzipped file is safely in place.
"""

import gzip
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator


@contextmanager
def atomic_write(target: Path, mode: str = "wb", **open_kwargs) -> Iterator[IO]:
    """Open target.partial for writing; rename to target only if the block finishes."""
    target = Path(target)
    partial = target.with_name(target.name + ".partial")
    try:
        with open(partial, mode, **open_kwargs) as handle:
            yield handle                                                        # your with-block runs here
        partial.replace(target)                                                 # the all-or-nothing step
    except BaseException:
        partial.unlink(missing_ok=True)                                         # never leave the half file behind
        raise


def gunzip_file(archive: Path, remove_archive: bool = True) -> Path:
    """Decompress archive.gz to archive (no .gz). Returns the new path."""
    archive = Path(archive)
    final = archive.with_suffix("")                                             # claims.txt.gz -> claims.txt
    with gzip.open(archive, "rb") as source, atomic_write(final) as target:
        shutil.copyfileobj(source, target)                                      # streams in chunks; fine for multi-GB files
    if remove_archive:
        archive.unlink()
    return final
