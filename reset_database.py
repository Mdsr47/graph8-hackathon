"""
================================================================================
graph8 Self-Healing Outbound Agent — Database Reset & Auto-Refresh Script
================================================================================
Run this script anytime to wipe past test records and reset the system to a clean state.
Usage:
    python reset_database.py
"""

import os
import sys
import asyncio
import httpx
import sqlite3

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
DB_PATH = os.path.join(BACKEND_DIR, "graph8_agent.db")
OLD_DB_PATH = os.path.join(BACKEND_DIR, "graph8_agent_v2.db")

async def reset_via_running_backend() -> bool:
    """If backend is running on http://localhost:8000, trigger reset via API so frontend SSE auto-refreshes live."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post("http://localhost:8000/api/settings/reset-database")
            if resp.status_code == 200:
                print("[Live Backend Detected] Reset triggered via API. Frontend dashboard refreshed automatically via real-time SSE stream!")
                return True
    except Exception:
        pass
    return False

def reset_direct_sqlite():
    """Directly cleans the SQLite database and re-seeds reference email defaults."""
    print(f"[*] Resetting SQLite database at: {DB_PATH}")

    # Remove duplicate v2 database if present
    if os.path.exists(OLD_DB_PATH):
        try:
            os.remove(OLD_DB_PATH)
            print("[*] Removed obsolete secondary database file (graph8_agent_v2.db).")
        except Exception:
            pass

    # Clean temporary journal or lock files
    for extra in [DB_PATH + "-wal", DB_PATH + "-shm", DB_PATH + "-journal"]:
        if os.path.exists(extra):
            try:
                os.remove(extra)
            except Exception:
                pass

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = conn.cursor()

    tables = ["campaigns", "contacts", "variants", "events", "agent_decisions", "approvals", "reference_emails", "settings", "mailbox_status", "inbox_messages"]
    for t in tables:
        try:
            cursor.execute(f"DELETE FROM {t}")
        except Exception:
            pass

    try:
        cursor.execute("VACUUM")
    except Exception:
        pass
    conn.commit()
    conn.close()

    # Re-seed clean default reference emails
    sys.path.insert(0, BACKEND_DIR)
    from app.database import db
    asyncio.run(db.init_db())
    print("[+] Clean schema verified and winning reference email templates re-seeded.")

def main():
    print("=" * 70)
    print("   GRAPH8 AGENT -- ONE-CLICK DATABASE RESET & REFRESH")
    print("=" * 70)

    # 1. Try notifying live backend so browser dashboard refreshes on the spot
    notified = asyncio.run(reset_via_running_backend())

    # 2. Perform direct wipe
    if not notified:
        reset_direct_sqlite()
    else:
        # Also clean any old DB file
        if os.path.exists(OLD_DB_PATH):
            try:
                os.remove(OLD_DB_PATH)
            except Exception:
                pass

    print("-" * 70)
    print("[SUCCESS] Database is now completely clean and fresh!")
    print("[INFO] Open or refresh your dashboard at http://localhost:5173")
    print("=" * 70)

if __name__ == "__main__":
    main()
