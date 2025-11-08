# Enhanced Search Integration Checklist
# 增強搜尋系統整合檢查清單

使用此檢查清單確保所有組件正確整合到您的應用程式中。

---

## 📦 檔案確認

### 新增檔案

- [ ] `components/enhanced_search.py` 已創建
- [ ] `callbacks/search_callbacks.py` 已創建
- [ ] `assets/enhanced_search_styles.css` 已創建
- [ ] `test_enhanced_search.py` 已創建（測試用）

### 文件檔案

- [ ] `ENHANCED_SEARCH_INTEGRATION.md` 已創建
- [ ] `SEARCH_ARCHITECTURE.md` 已創建
- [ ] `INTEGRATION_CHECKLIST.md` 已創建（本檔案）

---

## 🔧 程式碼修改

### Step 1: 修改 `app.py` 導入區塊

在檔案頂部添加：

```python
# === 新增導入 ===
from components.enhanced_search import (
    create_enhanced_search_bar,
    create_search_stores
)
from callbacks.search_callbacks import register_search_callbacks
```

- [ ] 導入語句已添加
- [ ] 無 import 錯誤

### Step 2: 修改 Dash App 初始化

找到 `app = Dash(__name__, ...)` 並修改為：

```python
app = Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    '/assets/voyage_styles.css',
    '/assets/enhanced_search_styles.css'  # ← 新增這一行
],
           title='Voyage - Your Journey, Perfectly Planned',
           suppress_callback_exceptions=True)
```

- [ ] 新 CSS 已添加到 external_stylesheets
- [ ] 應用啟動無錯誤

### Step 3: 修改 `app.layout`

在 `app.layout` 中添加搜尋 Stores：

```python
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Store(id='page-mode', data='login', storage_type='memory'),
    dcc.Store(id='current-page', data='overview', storage_type='memory'),
    dcc.Store(id='menu-open', data=False, storage_type='memory'),
    dcc.Store(id='view-mode', data='home', storage_type='memory'),
    dcc.Store(id='navigation-trigger', storage_type='memory'),

    # === 新增：搜尋系統 Stores ===
    create_search_stores(),  # ← 新增這一行

    html.Div(id='page-content', style={'minHeight': '100vh'})
], style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh'})
```

- [ ] `create_search_stores()` 已添加
- [ ] Layout 載入無錯誤

### Step 4: 替換搜尋欄組件

#### 4a. 在 `create_main_layout()` 函數中

找到第 281 行左右的 `create_compound_search_bar()`，替換為：

```python
# 原本：create_compound_search_bar()
# 替換為：
create_enhanced_search_bar(restaurants_df)
```

- [ ] 首頁搜尋欄已替換
- [ ] 首頁載入無錯誤

#### 4b. 在 `create_restaurant_list_page()` 函數中

找到第 396 行左右的 `create_compound_search_bar()`，替換為：

```python
# 原本：create_compound_search_bar()
# 替換為：
create_enhanced_search_bar(restaurants_df)
```

- [ ] 餐廳列表頁搜尋欄已替換
- [ ] 餐廳列表頁載入無錯誤

### Step 5: 註冊 Callbacks

在 `app.py` 的最後，`if __name__ == '__main__':` 之前添加：

```python
# === 註冊搜尋系統 Callbacks ===
register_search_callbacks(app, restaurants_df)

if __name__ == '__main__':
    app.run(debug=True)
```

- [ ] Callback 註冊語句已添加
- [ ] 應用啟動時無 callback 錯誤

### Step 6: 處理舊的 Callbacks（可選）

如果要完全使用新系統，可以註解掉以下舊 callbacks：

- `handle_search()` (第 911-938 行)
- `handle_restaurant_list_search()` (第 942-970 行)

**方式 1: 註解掉**
```python
# @app.callback(...)
# def handle_search(...):
#     ...
```

**方式 2: 完全刪除**

- [ ] 舊 callbacks 已處理
- [ ] 應用運行無衝突

---

## 🧪 功能測試

### 基本搜尋功能

- [ ] **關鍵字搜尋**
  - 輸入餐廳名稱可搜尋
  - 輸入料理類型可搜尋
  - 輸入車站名稱可搜尋

- [ ] **Dropdown 篩選器**
  - Cuisine dropdown 可正常選擇
  - Rating dropdown 可正常選擇
  - 組合篩選正確運作

- [ ] **搜尋按鈕**
  - 點擊搜尋返回結果
  - 無結果時顯示提示訊息

### 即時搜尋建議

- [ ] **建議顯示**
  - 輸入 2+ 字元顯示建議框
  - 建議包含餐廳、料理、地點
  - 最多顯示 8 個建議

- [ ] **建議互動**
  - Hover 建議項目有 highlight 效果
  - 點擊建議項目（如實作）填入搜尋框

- [ ] **清除按鈕**
  - 有輸入時顯示清除按鈕 (X)
  - 點擊清除按鈕清空搜尋框
  - 清空後建議框隱藏

### 進階篩選器

- [ ] **篩選器展開/收合**
  - 點擊 "Filters" 按鈕展開篩選器
  - 再次點擊收合篩選器
  - 按鈕有 active 狀態樣式

- [ ] **價格篩選**
  - 可選擇 Budget / Mid-range / Fine Dining
  - 多選正確運作
  - 篩選結果正確

- [ ] **地點篩選**
  - Dropdown 顯示所有車站
  - 可多選車站
  - 篩選結果正確

- [ ] **評論數篩選**
  - Slider 可拖動
  - 數值顯示正確
  - 篩選結果正確

- [ ] **排序功能**
  - 評分高到低排序正確
  - 評分低到高排序正確
  - 評論數排序正確
  - 名稱 A-Z 排序正確

- [ ] **清除全部篩選器**
  - 點擊 "Clear All Filters" 重設所有篩選器
  - 所有值回到預設狀態

### 篩選標籤 (Filter Chips)

- [ ] **標籤顯示**
  - 設定篩選器後顯示對應標籤
  - Cuisine 標籤正確顯示
  - Rating 標籤正確顯示 (⭐ 符號)
  - Price 標籤正確顯示
  - Station 標籤正確顯示
  - Review count 標籤正確顯示

- [ ] **標籤移除**
  - 點擊標籤上的 X 移除該篩選器
  - 移除後標籤消失
  - 對應的篩選器值清除
  - 搜尋結果自動更新（如實作）

### 搜尋歷史

- [ ] **歷史記錄**
  - 執行搜尋後記錄到歷史
  - 顯示最近 5 筆搜尋
  - 顯示相對時間（5m ago, 1h ago）

- [ ] **歷史重播**
  - 點擊歷史項目填入關鍵字
  - 自動觸發搜尋（如實作）

- [ ] **Session 持久化**
  - 重新整理頁面後歷史保留
  - 關閉瀏覽器後歷史清除

### 熱門搜尋

- [ ] **熱門統計**
  - 多次搜尋相同詞增加計數
  - 顯示前 5 個熱門項目
  - 顯示搜尋次數

- [ ] **熱門項目點擊**
  - 點擊熱門項目執行搜尋
  - 搜尋詞正確填入

- [ ] **Local Storage 持久化**
  - 關閉瀏覽器後熱門統計保留
  - 多次訪問累計計數

---

## 🎨 樣式檢查

### 視覺外觀

- [ ] **搜尋欄**
  - 深色背景 (rgba(26, 26, 26, 0.95))
  - 金色邊框 (rgba(222, 181, 34, 0.2))
  - 圓角 60px
  - Icon 顯示正確

- [ ] **建議框**
  - 位置正確（搜尋欄下方）
  - 背景半透明
  - Hover 效果正常
  - 捲軸樣式正確（金色）

- [ ] **進階篩選器**
  - Grid 布局正確
  - 背景色正確
  - Checkbox/Radio 使用金色 accent
  - Slider 樣式正確

- [ ] **篩選標籤**
  - 金色邊框和背景
  - Hover 效果正常
  - X 按鈕可點擊
  - 動畫效果流暢

- [ ] **搜尋歷史/熱門**
  - 兩欄布局
  - Icon 顯示正確
  - Hover 效果正常
  - 字體顏色對比足夠

### 響應式設計

- [ ] **桌面 (>1024px)**
  - 搜尋欄單行顯示
  - 進階篩選器多欄 grid
  - 所有元素正確對齊

- [ ] **平板 (768-1024px)**
  - 搜尋欄換行顯示
  - 進階篩選器單欄
  - 字體大小適中

- [ ] **手機 (<768px)**
  - 搜尋欄垂直排列
  - 按鈕全寬顯示
  - 建議框高度限制
  - 觸控目標足夠大

---

## ⚡ 效能檢查

- [ ] **即時建議**
  - 輸入後 < 500ms 顯示建議
  - 無明顯延遲或卡頓

- [ ] **搜尋執行**
  - 點擊搜尋後 < 1s 返回結果
  - 大量結果不卡頓（分頁）

- [ ] **防抖動**
  - 快速輸入時不頻繁觸發
  - Debounce 300ms 生效

- [ ] **記憶體使用**
  - 長時間使用無記憶體洩漏
  - Store 資料量合理（歷史最多 10 筆）

---

## 🐛 錯誤處理

- [ ] **空值處理**
  - 無關鍵字時可搜尋（顯示全部）
  - 無篩選器時正常運作

- [ ] **異常輸入**
  - 超長關鍵字不崩潰
  - 特殊字元正確處理（& < > " '）

- [ ] **無結果**
  - 顯示友善的空狀態訊息
  - 建議調整搜尋條件

- [ ] **網路錯誤**
  - 資料載入失敗有提示（如適用）

---

## 🔒 安全性檢查

- [ ] **XSS 防護**
  - 使用者輸入不執行腳本
  - HTML 特殊字元正確 escape

- [ ] **SQL 注入**
  - 使用 pandas 方法，無直接 SQL 拼接
  - 參數化查詢（如使用資料庫）

- [ ] **輸入驗證**
  - 關鍵字長度限制
  - 數值範圍檢查

---

## 📱 無障礙 (Accessibility)

- [ ] **鍵盤導航**
  - Tab 可切換所有元素
  - Enter 可執行搜尋
  - Esc 關閉建議框（如實作）

- [ ] **螢幕閱讀器**
  - 所有互動元素有適當 label
  - ARIA 屬性正確設定（如適用）

- [ ] **顏色對比**
  - 文字和背景對比 >= 4.5:1
  - 金色在深色背景清晰可見

- [ ] **焦點指示**
  - 焦點元素有清晰邊框
  - 焦點順序符合邏輯

---

## 📊 瀏覽器相容性

- [ ] **Chrome/Edge (Chromium)**
  - 所有功能正常
  - 樣式正確顯示

- [ ] **Firefox**
  - 所有功能正常
  - 樣式正確顯示

- [ ] **Safari**
  - 所有功能正常
  - 樣式正確顯示（尤其 backdrop-filter）

- [ ] **行動瀏覽器**
  - iOS Safari 正常運作
  - Android Chrome 正常運作

---

## 🧹 程式碼品質

- [ ] **無 Console 錯誤**
  - 開發者工具無紅色錯誤
  - 無 callback 警告

- [ ] **無 Linting 警告**
  - Python 程式碼符合 PEP 8
  - 無未使用的導入

- [ ] **註解清晰**
  - 關鍵邏輯有中英文註解
  - Docstrings 完整

- [ ] **命名一致**
  - 變數命名清晰有意義
  - ID 命名遵循 kebab-case

---

## 📚 文件完整性

- [ ] **整合指南**
  - `ENHANCED_SEARCH_INTEGRATION.md` 可讀
  - 步驟清晰完整

- [ ] **架構文件**
  - `SEARCH_ARCHITECTURE.md` 可讀
  - 流程圖清楚

- [ ] **程式碼註解**
  - `enhanced_search.py` 有詳細註解
  - `search_callbacks.py` 有詳細註解

- [ ] **README 更新**
  - 主 `README.md` 或 `CLAUDE.md` 已更新
  - 提及新增的搜尋功能

---

## 🚀 部署前檢查

- [ ] **環境變數**
  - 無硬編碼的敏感資訊
  - 使用 `.env` 檔案（如適用）

- [ ] **依賴套件**
  - `requirements.txt` 已更新
  - 所有套件版本鎖定

- [ ] **靜態資源**
  - `assets/` 資料夾包含所有 CSS
  - 圖片資源正確載入

- [ ] **資料檔案**
  - `data/Kyoto_Restaurant_Info_Full.csv` 存在
  - 欄位名稱正確

---

## ✅ 最終確認

- [ ] 所有上述項目已檢查完畢
- [ ] 測試應用 (`test_enhanced_search.py`) 正常運行
- [ ] 主應用 (`app.py`) 正常運行
- [ ] 無 Console 錯誤或警告
- [ ] 效能符合預期
- [ ] 準備好部署或提交

---

## 🆘 遇到問題？

如果遇到問題，請參考：

1. **整合指南**: `ENHANCED_SEARCH_INTEGRATION.md` → 疑難排解章節
2. **架構文件**: `SEARCH_ARCHITECTURE.md` → 錯誤處理章節
3. **測試應用**: 運行 `test_enhanced_search.py` 單獨測試功能
4. **主文件**: 查閱 `CLAUDE.md` 專案整體說明

---

## 📝 記錄

完成日期: _______________

完成者: _______________

備註:
```
_________________________________________
_________________________________________
_________________________________________
```

---

**檢查清單版本**: 1.0.0
**最後更新**: 2025-11-05
**維護者**: Claude (Anthropic)
