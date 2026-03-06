"""Background archiver — watches Kiro CLI DB and snapshots sessions to disk.

Runs as a persistent background process (launchd on macOS, systemd on Linux).
Polls the DB file's mtime every 10s and archives any new/updated conversations
to ~/.kiro_sessions/<conversation_id>.json.
"""

import json, sys, os, time, signal
from . import CLI_DB, SESSIONS_DIR, query

def ensure_sessions_dir():
    SESSIONS_DIR.mkdir(exist_ok=True)

def archive_sessions():
    """Snapshot all live conversations from the CLI DB into ~/.kiro_sessions/."""
    ensure_sessions_dir()
    rows = query(CLI_DB, """
        SELECT conversation_id, key as cwd, created_at, updated_at, value
        FROM conversations_v2
    """)
    archived = 0
    for row in rows:
        path = SESSIONS_DIR / "{}.json".format(row["conversation_id"])
        if path.exists():
            try:
                existing = json.loads(path.read_text())
                if existing.get("updated_at") >= row["updated_at"]:
                    continue
            except (json.JSONDecodeError, KeyError):
                pass
        snapshot = {
            "conversation_id": row["conversation_id"],
            "cwd": row["cwd"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "value": json.loads(row["value"]),
        }
        path.write_text(json.dumps(snapshot, separators=(",", ":")))
        archived += 1
    return archived

def load_archived_sessions(cutoff_ms=None):
    """Load all snapshots from ~/.kiro_sessions/."""
    ensure_sessions_dir()
    sessions = []
    for path in SESSIONS_DIR.glob("*.json"):
        if cutoff_ms:
            mtime_ms = int(path.stat().st_mtime * 1000)
            if mtime_ms < cutoff_ms:
                continue
        try:
            sessions.append(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return sessions

def _log(msg):
    sys.stderr.write("[kiro-archiver] {}\n".format(msg))
    sys.stderr.flush()

def main():
    """Poll CLI_DB mtime every 10s, archive on change."""
    running = True
    def _stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    interval = int(os.environ.get("KIRO_ARCHIVE_INTERVAL", "10"))
    _log("started — watching {} every {}s".format(CLI_DB, interval))

    last_mtime = 0.0
    while running:
        try:
            if CLI_DB.exists():
                mtime = CLI_DB.stat().st_mtime
                if mtime != last_mtime:
                    last_mtime = mtime
                    n = archive_sessions()
                    if n:
                        _log("archived {} session(s)".format(n))
        except Exception as e:
            _log("error: {}".format(e))
        # Sleep in small increments so SIGTERM is responsive
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)

    _log("stopped")

if __name__ == "__main__":
    main()
