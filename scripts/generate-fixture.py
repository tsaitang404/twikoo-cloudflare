#!/usr/bin/env python3
"""Generate a disposable, representative Twikoo D1 SQLite database."""
from pathlib import Path
import argparse
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="/tmp/twikoo-validation.sqlite")
    parser.add_argument("--break-integrity", action="store_true",
                        help="add intentional defects to exercise the audit")
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        parser.error(f"refusing to overwrite existing file: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(output)
    db.executescript((ROOT / "migrations/0001_baseline.sql").read_text())
    columns = "_id, uid, nick, mail, mailMd5, link, ua, ip, ipRegion, master, url, href, comment, pid, rid, isSpam, created, updated, like, top, avatar"

    def insert(cid, url, created, pid="", rid="", likes="[]"):
        values = (cid, "fixture-user", "Fixture", "", "", "", "test-agent", "", "", 0,
                  url, "", "Fixture comment body", pid, rid, 0, created, created, likes, 0, "")
        db.execute(f"INSERT INTO comment ({columns}) VALUES ({','.join('?' for _ in values)})", values)

    insert("fixture-root", "/migration-validation/article", 1730000000000)
    insert("fixture-reply", "/migration-validation/article", 1730000001000,
           pid="fixture-root", rid="fixture-root", likes='["fixture-user"]')
    db.execute("INSERT INTO config (value) VALUES (?)", ('{"enabled":true}',))
    db.execute("INSERT INTO counter (url, title, time, created, updated) VALUES (?, ?, ?, ?, ?)",
               ("/migration-validation/article", "Fixture article", 1730000001, 1730000000, 1730000001))
    if args.break_integrity:
        insert("fixture-broken", "", 1730000002000, pid="absent-parent", rid="absent-root", likes="invalid-json")
        insert("fixture-root", "/migration-validation/duplicate", 1730000003000)
    db.commit()
    print(f"Created {output} (fixture only; rows: {db.execute('SELECT count(*) FROM comment').fetchone()[0]})")
    db.close()


if __name__ == "__main__":
    main()
