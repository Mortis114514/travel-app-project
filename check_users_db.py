"""
Check users.db database structure and data
"""
import sqlite3
from datetime import datetime

def check_users_db():
    """Check users database for issues"""

    db_path = './data/users.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 60)
    print("USERS DATABASE CHECK")
    print("=" * 60)

    # Check users table structure
    print("\n[USERS TABLE STRUCTURE]")
    cursor.execute('PRAGMA table_info(users)')
    cols = cursor.fetchall()
    for col in cols:
        print(f"  {col[1]:20} {col[2]:15} NOT NULL: {bool(col[3])}, PK: {bool(col[5])}")

    # Check users data
    print("\n[USERS TABLE DATA]")
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    print(f"  Total users: {len(users)}")

    if users:
        print("\n  User details:")
        cursor.execute('SELECT id, username, email, created_at, last_login FROM users')
        for user in cursor.fetchall():
            print(f"    ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
            print(f"        Created: {user[3]}, Last Login: {user[4]}")

    # Check sessions table structure
    print("\n[SESSIONS TABLE STRUCTURE]")
    cursor.execute('PRAGMA table_info(sessions)')
    cols = cursor.fetchall()
    for col in cols:
        print(f"  {col[1]:20} {col[2]:15} NOT NULL: {bool(col[3])}, PK: {bool(col[5])}")

    # Check sessions data
    print("\n[SESSIONS TABLE DATA]")
    cursor.execute('SELECT COUNT(*) FROM sessions')
    session_count = cursor.fetchone()[0]
    print(f"  Total sessions: {session_count}")

    if session_count > 0:
        print("\n  Active sessions:")
        cursor.execute('SELECT session_id, user_id, created_at, expires_at FROM sessions')
        for session in cursor.fetchall():
            print(f"    Session: {session[0][:20]}...")
            print(f"        User ID: {session[1]}, Created: {session[2]}, Expires: {session[3]}")

    # Check for potential issues
    print("\n[POTENTIAL ISSUES CHECK]")
    issues = []

    # Check for users without email
    cursor.execute('SELECT COUNT(*) FROM users WHERE email IS NULL OR email = ""')
    no_email = cursor.fetchone()[0]
    if no_email > 0:
        issues.append(f"  - {no_email} users without email")

    # Check for duplicate usernames
    cursor.execute('SELECT username, COUNT(*) as cnt FROM users GROUP BY username HAVING cnt > 1')
    duplicates = cursor.fetchall()
    if duplicates:
        issues.append(f"  - Duplicate usernames found: {[d[0] for d in duplicates]}")

    # Check for expired sessions that weren't cleaned
    cursor.execute('SELECT COUNT(*) FROM sessions WHERE datetime(expires_at) < datetime("now")')
    expired = cursor.fetchone()[0]
    if expired > 0:
        issues.append(f"  - {expired} expired sessions (should be cleaned)")

    # Check for sessions with invalid user_id
    cursor.execute('SELECT COUNT(*) FROM sessions WHERE user_id NOT IN (SELECT id FROM users)')
    orphan_sessions = cursor.fetchone()[0]
    if orphan_sessions > 0:
        issues.append(f"  - {orphan_sessions} orphaned sessions (user doesn't exist)")

    if issues:
        print("  Issues found:")
        for issue in issues:
            print(issue)
    else:
        print("  No issues found!")

    conn.close()

    print("\n" + "=" * 60)

if __name__ == '__main__':
    check_users_db()
