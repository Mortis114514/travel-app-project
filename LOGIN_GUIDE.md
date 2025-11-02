# 登入系統使用指南

## 概述

本旅遊數據分析平台已整合完整的使用者認證系統，包含以下功能：

- 使用者登入/登出
- 使用者註冊
- Session 管理（支援「記住我」功能）
- 頁面訪問保護
- SQLite 使用者資料庫

## 安裝與設置

1. **安裝相依套件**：
   ```bash
   pip install -r requirements.txt
   ```

2. **啟動應用程式**：
   ```bash
   python app.py
   ```

3. **開啟瀏覽器**：
   訪問 `http://127.0.0.1:8050`

## 使用說明

### 登入

應用程式啟動後會自動顯示登入頁面。系統預設已建立兩個測試帳號：

- **管理員帳號**
  - 使用者名稱：`admin`
  - 密碼：`admin123`

- **示範帳號**
  - 使用者名稱：`demo`
  - 密碼：`demo123`

### 記住我功能

- 勾選「記住我」：Session 有效期為 30 天
- 不勾選：Session 有效期為 2 小時

### 註冊新帳號

1. 在登入頁面點擊「立即註冊」連結
2. 填寫以下資訊：
   - 使用者名稱（必填）
   - 電子郵件（選填）
   - 密碼（必填，至少 6 個字元）
   - 確認密碼（必填）
3. 點擊「註冊」按鈕
4. 註冊成功後返回登入頁面進行登入

### 登出

在應用程式右上角點擊「登出」按鈕即可登出系統。

## 系統架構

### 檔案結構

```
travel-app-project/
├── app.py                    # 主應用程式（含認證邏輯）
├── utils/
│   ├── auth.py              # 認證模組
│   ├── data_validation.py
│   ├── data_transform.py
│   ├── data_clean.py
│   ├── visualization.py
│   └── const.py
├── pages/
│   └── login_page.py        # 登入/註冊頁面 UI
├── data/
│   ├── users.db             # 使用者資料庫（自動建立）
│   ├── Travel_dataset.csv
│   ├── country_info.csv
│   └── Attractions.csv
└── requirements.txt
```

### 資料庫結構

**users 表**：
- `id`: 使用者 ID（主鍵）
- `username`: 使用者名稱（唯一）
- `password_hash`: SHA-256 雜湊密碼
- `email`: 電子郵件
- `created_at`: 建立時間
- `last_login`: 最後登入時間

**sessions 表**：
- `session_id`: Session ID（主鍵）
- `user_id`: 使用者 ID（外鍵）
- `created_at`: 建立時間
- `expires_at`: 過期時間

### 認證流程

1. **使用者登入**：
   - 輸入使用者名稱和密碼
   - 系統驗證憑證（SHA-256 雜湊比對）
   - 建立 Session 並儲存到資料庫
   - 將 Session ID 儲存到瀏覽器的 session storage

2. **頁面訪問**：
   - 每次頁面載入時檢查 session storage
   - 驗證 Session ID 是否有效且未過期
   - 有效：顯示主應用程式
   - 無效：導向登入頁面

3. **使用者登出**：
   - 從資料庫刪除 Session 記錄
   - 清除 session storage
   - 導向登入頁面

### 安全性特點

1. **密碼加密**：使用 SHA-256 雜湊演算法，密碼不以明文儲存
2. **Session 管理**：使用 UUID 生成唯一 Session ID
3. **過期機制**：自動清理過期的 Sessions
4. **輸入驗證**：註冊時檢查密碼長度和一致性

## 自訂設定

### 修改 Session 過期時間

在 `app.py` 的 `login()` callback 中修改：

```python
# 不記住我：預設 2 小時
expires_at = datetime.now() + timedelta(hours=2)

# 記住我：預設 30 天
expires_at = datetime.now() + timedelta(days=30)
```

### 修改密碼強度要求

在 `app.py` 的 `register()` callback 中修改：

```python
if len(password) < 6:  # 修改此處的數字
    return dbc.Alert('密碼至少需要 6 個字元', color='danger')
```

### 刪除測試帳號

在 `utils/auth.py` 的底部移除或註解以下程式碼：

```python
# 建立預設管理員帳號（僅供測試使用，生產環境應移除）
try:
    create_user('admin', 'admin123', 'admin@example.com')
    create_user('demo', 'demo123', 'demo@example.com')
except:
    pass
```

## 生產環境部署建議

1. **更換密碼雜湊演算法**：考慮使用 bcrypt 或 argon2 替代 SHA-256
2. **啟用 HTTPS**：保護傳輸中的敏感資訊
3. **設定速率限制**：防止暴力破解攻擊
4. **使用環境變數**：儲存資料庫路徑等敏感設定
5. **實施日誌記錄**：記錄登入嘗試和安全事件
6. **定期備份**：定期備份 users.db 資料庫

## 故障排除

### 無法登入

1. 確認使用者名稱和密碼正確
2. 檢查 `data/users.db` 是否存在
3. 檢查瀏覽器是否啟用 session storage

### 資料庫錯誤

1. 刪除 `data/users.db` 並重新啟動應用程式
2. 系統會自動重新建立資料庫和預設帳號

### Session 過期問題

1. 檢查系統時間是否正確
2. 確認 `clean_expired_sessions()` 功能正常運作

## 技術支援

如有任何問題或建議，請查看專案文件或聯繫開發團隊。
