#!/usr/bin/env python3
"""Exercise the read-only data audit using disposable SQLite fixtures."""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "migrations" / "0001_baseline.sql"
AUDIT = ROOT / "scripts" / "validate-data.sql"
FIELDS = (
    "_id, uid, nick, mail, mailMd5, link, ua, ip, ipRegion, master, url, href, "
    "comment, pid, rid, isSpam, created, updated, like, top, avatar"
)


def add_comment(db, *, cid, url, created, pid="", rid="", likes="[]"):
    values = (cid, "u", "n", "", "", "", "", "", "", 0, url, "", "text",
              pid, rid, 0, created, created, likes, 0, "")
    db.execute(f"INSERT INTO comment ({FIELDS}) VALUES ({','.join('?' for _ in values)})", values)


def findings(db):
    audit = AUDIT.read_text().split("-- Inspect the schema", 1)[0]
    rows = [db.execute(stmt).fetchone() for stmt in audit.split(";") if stmt.strip()]
    return {name: (count, examples) for name, count, examples in rows}


def main():
    db = sqlite3.connect(":memory:")
    db.executescript(BASELINE.read_text())
    add_comment(db, cid="root", url="/article", created=1)
    add_comment(db, cid="reply", url="/article", created=2, pid="root", rid="root")
    report = findings(db)
    assert report["comment_rows"][0] == 2
    assert report["duplicate_comment_ids"][0] == 0
    assert report["reply_missing_root"][0] == 0
    assert report["reply_missing_parent"][0] == 0
    assert report["invalid_like_json"][0] == 0

    add_comment(db, cid="broken", url="", created=3, pid="absent", rid="absent", likes="not-json")
    report = findings(db)
    assert report["empty_article_url"][0] == 1
    assert report["reply_missing_root"][0] == 1
    assert report["reply_missing_parent"][0] == 1
    assert report["invalid_like_json"][0] == 1

    add_comment(db, cid="root", url="/different", created=4)
    assert findings(db)["duplicate_comment_ids"][0] == 1
    print("PASS: baseline schema and read-only integrity diagnostics detect valid and invalid fixtures")


if __name__ == "__main__":
    main()
