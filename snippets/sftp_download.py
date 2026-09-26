r""" README
Purpose: Download files from an SFTP server using a private key, verifying the server's identity first.
Output: Returns the list of local paths downloaded.
Personal Variables: Find "#!REPLACE" comments to locate.
Implementation:
    Paste this block into your script. Get the credentials with credentials.py:
        USER, KEY, PASSPHRASE = load_credentials("XIFIN_SFTP_USER", "XIFIN_SFTP_KEY", "XIFIN_SFTP_PASSPHRASE")
        newest = find_latest_folder_date(OUTPUT_ROOT)                           # None on the very first run
        cutoff = newest + timedelta(days=1) if newest else None                 # XiFin: a file is dated the day AFTER its folder
        got = sftp_download(
            user=USER, key_path=KEY, passphrase=PASSPHRASE,
            remote_dir="/prod/from_xifin/incremental_extract/",
            local_dir=INPUT_DIR,
            want=lambda name: (d := find_date_in_filename(name)) is not None and (cutoff is None or d > cutoff),
        )
    `want` decides which remote files to fetch. Leave it out to fetch everything.
    Sub-folders on the server are skipped; only files in remote_dir itself are downloaded.
CRITICAL - `want` is what stops daily re-downloads:
    The "already downloaded" check only looks for NAME in local_dir. Once a file is unzipped
    (gunzip_file deletes the .gz), renamed, or moved to another folder, it no longer counts as downloaded.
    If the server keeps old files, `want` must exclude them (e.g. by date, as above, with the cutoff
    taken from find_latest_folder_date), or every run downloads the whole folder again.
Setup - host key (do this ONCE per machine, from Command Prompt - not PowerShell):
    ssh-keyscan -p 22 sftp.example.com > "C:\path\to\known_hosts"
    Then point KNOWN_HOSTS at that file.
    PowerShell's > writes the file as UTF-16, which paramiko can't read.
CRITICAL - why the host key matters:
    AutoAddPolicy (used in the original script) trusts WHATEVER server answers, so a spoofed server
    would receive your login and hand you its files. RejectPolicy refuses any server not in known_hosts.
    If the vendor rotates their key, the download fails loudly with "not found in known_hosts" -
    re-run ssh-keyscan after confirming the change with them.
Behavior:
    Files still sitting in local_dir are skipped, so a re-run after a crash doesn't fetch them twice.
    Each file lands as NAME.partial first and is renamed only when complete, so a dropped connection
    never leaves a half file that looks finished.
    Connections close in finally blocks, even on error.
Requires: pip install paramiko
"""

import logging
import stat
from pathlib import Path
from typing import Callable

import paramiko

HOST = "sftp.example.com"                                                       #!REPLACE - SFTP server name
PORT = 22                                                                       #!REPLACE - usually 22
KNOWN_HOSTS = Path(r"C:\path\to\known_hosts")                                   #!REPLACE - file created by ssh-keyscan above


def _load_key(key_path: str, passphrase: str | None) -> paramiko.PKey:
    """Load an RSA, Ed25519 or ECDSA private key, whichever the file is."""
    for key_class in (paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey):
        try:
            return key_class.from_private_key_file(key_path, password=passphrase)
        except paramiko.SSHException:
            continue                                                            # wrong type - try the next one
    raise ValueError(f"Could not read private key (wrong passphrase or unsupported type): {key_path}")


def sftp_download(
    user: str,
    key_path: str,
    passphrase: str | None,
    remote_dir: str,
    local_dir: Path,
    want: Callable[[str], bool] = lambda name: True,
) -> list[Path]:
    """Download every file in remote_dir for which want(name) is True."""
    local_dir = Path(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []

    client = paramiko.SSHClient()
    client.load_host_keys(str(KNOWN_HOSTS))                                     # the servers we trust
    client.set_missing_host_key_policy(paramiko.RejectPolicy())                 # refuse anything else
    try:
        client.connect(HOST, port=PORT, username=user,
                       pkey=_load_key(key_path, passphrase), timeout=60)
        sftp = client.open_sftp()
        try:
            for entry in sorted(sftp.listdir_attr(remote_dir), key=lambda e: e.filename):
                name = entry.filename
                if entry.st_mode is not None and stat.S_ISDIR(entry.st_mode):
                    continue                                                    # a sub-folder, not a file
                if not want(name):
                    continue
                target = local_dir / name
                if target.exists():
                    logging.info("Already downloaded: %s", name)
                    continue
                partial = target.with_name(name + ".partial")
                try:
                    sftp.get(f"{remote_dir.rstrip('/')}/{name}", str(partial))
                except Exception:
                    partial.unlink(missing_ok=True)                             # don't leave a half file behind
                    raise
                partial.replace(target)                                         # rename only once the whole file is here
                logging.info("Downloaded: %s", name)
                downloaded.append(target)
        finally:
            sftp.close()
    finally:
        client.close()
    return downloaded
