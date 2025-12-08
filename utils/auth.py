import sqlite3
import hashlib
import os
from datetime import datetime

# 資料庫檔案路徑
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.db')

def init_db():
    """初始化使用者資料庫"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 建立使用者表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            profile_photo TEXT
        )
    ''')

    # 建立 session 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()

    # Add profile_photo column if it doesn't exist (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.close()

def hash_password(password):
    """使用 SHA-256 雜湊密碼"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, email=None):
    """建立新使用者"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        password_hash = hash_password(password)

        cursor.execute(
            'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
            (username, password_hash, email)
        )
        conn.commit()
        conn.close()
        return True, "使用者建立成功"
    except sqlite3.IntegrityError:
        return False, "使用者名稱已存在"
    except Exception as e:
        return False, f"建立失敗: {str(e)}"

def verify_user(username, password):
    """驗證使用者登入"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    password_hash = hash_password(password)
    cursor.execute(
        'SELECT id, username FROM users WHERE username = ? AND password_hash = ?',
        (username, password_hash)
    )

    user = cursor.fetchone()

    if user:
        # 更新最後登入時間
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE id = ?',
            (datetime.now(), user[0])
        )
        conn.commit()

    conn.close()
    return user  # 返回 (user_id, username) 或 None

def get_user_by_id(user_id):
    """根據 ID 取得使用者"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    conn.close()
    return user

def get_user_full_details(user_id):
    """取得使用者完整資訊，包含建立時間和最後登入時間"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id, username, email, created_at, last_login, profile_photo FROM users WHERE id = ?',
        (user_id,)
    )
    user = cursor.fetchone()

    conn.close()

    if user:
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at'],
            'last_login': user['last_login'],
            'profile_photo': user['profile_photo']
        }
    return None

def update_profile_photo(user_id, photo_data):
    """更新使用者的個人照片（base64 編碼）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE users SET profile_photo = ? WHERE id = ?',
            (photo_data, user_id)
        )

        conn.commit()
        conn.close()
        return True, "照片更新成功"
    except Exception as e:
        return False, f"更新失敗: {str(e)}"

def create_session(user_id, session_id, expires_at):
    """建立 session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)',
        (session_id, user_id, expires_at)
    )

    conn.commit()
    conn.close()

def get_session(session_id):
    """取得 session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        'SELECT user_id, expires_at FROM sessions WHERE session_id = ?',
        (session_id,)
    )

    session = cursor.fetchone()
    conn.close()

    if session:
        user_id, expires_at = session
        expires_at = datetime.fromisoformat(expires_at)

        # 檢查是否過期
        if expires_at > datetime.now():
            return user_id

    return None

def delete_session(session_id):
    """刪除 session（登出）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))

    conn.commit()
    conn.close()

def clean_expired_sessions():
    """清理過期的 sessions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM sessions WHERE expires_at < ?', (datetime.now(),))

    conn.commit()
    conn.close()

# 初始化資料庫
init_db()

# 建立預設管理員帳號（僅供測試使用，生產環境應移除）
try:
    create_user('admin', 'admin123', 'admin@example.com')
    create_user('demo', 'demo123', 'demo@example.com')
except:
    pass  # 如果帳號已存在就忽略
