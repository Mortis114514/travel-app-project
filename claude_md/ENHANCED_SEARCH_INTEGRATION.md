# Enhanced Search System Integration Guide
# 增強搜尋系統整合指南

本文件說明如何將新的增強搜尋系統整合到現有的 Voyage 應用程式中。

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [檔案結構](#檔案結構)
3. [整合步驟](#整合步驟)
4. [Callback 架構](#callback-架構)
5. [State Management](#state-management)
6. [使用範例](#使用範例)
7. [樣式客製化](#樣式客製化)
8. [疑難排解](#疑難排解)

---

## 系統概述

### 功能特色

#### 1. **即時搜尋建議 (Real-time Search Suggestions)**
- 使用者輸入時自動顯示匹配建議
- 搜尋範圍：餐廳名稱、料理類型、車站地點
- 防抖動機制：300ms debounce
- 最多顯示 8 個建議項目

#### 2. **進階篩選器 (Advanced Filters)**
- **價格範圍**: Budget / Mid-range / Fine Dining
- **地點篩選**: 多選車站/地區
- **評論數量**: 0-200+ 滑桿篩選
- **排序選項**: 評分高低、評論數、名稱

#### 3. **篩選標籤 (Filter Chips)**
- 即時顯示當前活躍的篩選條件
- 可單獨移除任一篩選標籤
- 支援「清除全部」功能

#### 4. **搜尋歷史 (Search History)**
- 自動記錄最近 10 次搜尋
- 顯示搜尋時間（相對時間）
- 點擊可快速重新執行搜尋
- Session storage 儲存（瀏覽器關閉後清除）

#### 5. **熱門搜尋 (Popular Searches)**
- 統計搜尋詞出現頻率
- 顯示前 5 個熱門項目
- Local storage 儲存（長期保留）
- 包含預設熱門項目

#### 6. **即時搜尋 (Live Search)**
- 輸入改變時自動觸發搜尋（可選功能）
- 配合 debounce 防止過度請求
- 適用於餐廳列表頁

---

## 檔案結構

```
travel-app-project/
├── components/
│   └── enhanced_search.py          # 搜尋組件定義
├── callbacks/
│   └── search_callbacks.py         # 搜尋 Callback 函數
├── assets/
│   ├── voyage_styles.css           # 現有樣式
│   └── enhanced_search_styles.css  # 新增搜尋樣式
├── app.py                          # 主應用程式（需修改）
└── ENHANCED_SEARCH_INTEGRATION.md  # 本文件
```

---

## 整合步驟

### Step 1: 安裝必要套件（如果尚未安裝）

```bash
pip install dash dash-bootstrap-components pandas
```

### Step 2: 修改 `app.py` - 導入新模組

在 `app.py` 頂部添加導入：

```python
# 在現有 import 後面添加
from components.enhanced_search import (
    create_enhanced_search_bar,
    create_search_stores
)
from callbacks.search_callbacks import register_search_callbacks
```

### Step 3: 修改 `app.py` - 添加外部樣式

在 Dash 初始化部分修改：

```python
app = Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    '/assets/voyage_styles.css',
    '/assets/enhanced_search_styles.css'  # 新增這一行
],
           title='Voyage - Your Journey, Perfectly Planned',
           suppress_callback_exceptions=True)
```

### Step 4: 修改 `app.py` - 更新 app.layout

在 `app.layout` 中添加搜尋相關的 Stores：

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
    create_search_stores(),

    html.Div(id='page-content', style={'minHeight': '100vh'})
], style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh'})
```

### Step 5: 修改 `app.py` - 替換搜尋欄組件

找到 `create_main_layout()` 和 `create_restaurant_list_page()` 函數中的搜尋欄，替換為：

**原本的程式碼（第 281 行）:**
```python
create_compound_search_bar()
```

**替換為:**
```python
create_enhanced_search_bar(restaurants_df)
```

**同樣在 `create_restaurant_list_page()` 函數（第 396 行）中也要替換。**

### Step 6: 註冊 Callbacks

在 `app.py` 的最後，`if __name__ == '__main__':` 之前添加：

```python
# === 註冊搜尋系統 Callbacks ===
register_search_callbacks(app, restaurants_df)

if __name__ == '__main__':
    app.run(debug=True)
```

### Step 7: 移除舊的搜尋相關 Callback（可選）

如果要完全使用新系統，可以註解掉或移除原有的 `handle_search()` callback（第 911-938 行）和 `handle_restaurant_list_search()` callback（第 942-970 行）。

**注意**: 新系統中的 `handle_comprehensive_search()` callback 已經完全取代這兩個功能。

---

## Callback 架構

### Callback 流程圖

```
使用者輸入關鍵字
    ↓
[1] update_search_suggestions
    → 生成即時建議列表
    → 顯示/隱藏建議框

使用者點擊「進階篩選」
    ↓
[2] toggle_advanced_filters
    → 展開/收合篩選器區塊

使用者設定篩選條件
    ↓
[5] update_filter_chips
    → 生成活躍篩選標籤

使用者點擊「搜尋」按鈕
    ↓
[7] handle_comprehensive_search
    → 執行搜尋邏輯
    → 更新搜尋結果
    → 記錄搜尋歷史
    → 更新熱門搜尋統計
    ↓
[8] display_search_history
    → 顯示搜尋歷史列表
    ↓
[9] display_popular_searches
    → 顯示熱門搜尋列表
```

### 主要 Callbacks 說明

#### 1. `update_search_suggestions`
- **觸發**: `search-destination.value` 改變
- **輸出**: 建議列表、顯示狀態、清除按鈕
- **功能**: 即時生成搜尋建議

#### 2. `toggle_advanced_filters`
- **觸發**: `toggle-advanced-filters.n_clicks`
- **輸出**: 摺疊狀態、按鈕樣式、開關狀態
- **功能**: 切換進階篩選器顯示

#### 3. `clear_search_input`
- **觸發**: `clear-search-btn.n_clicks`
- **輸出**: 清空搜尋框
- **功能**: 清除關鍵字輸入

#### 4. `clear_all_filters`
- **觸發**: `clear-filters-btn.n_clicks`
- **輸出**: 重設所有篩選器
- **功能**: 一鍵清除所有篩選條件

#### 5. `update_filter_chips`
- **觸發**: 任一篩選器值改變
- **輸出**: 篩選標籤列表
- **功能**: 即時顯示當前篩選條件

#### 6. `remove_filter_chip`
- **觸發**: 點擊標籤的移除按鈕（Pattern Matching）
- **輸出**: 更新對應的篩選器值
- **功能**: 移除單個篩選條件

#### 7. `handle_comprehensive_search` ⭐ 核心功能
- **觸發**:
  - `search-btn.n_clicks` (手動搜尋)
  - `search-trigger.data` (即時搜尋)
- **輸出**:
  - 搜尋結果
  - 當前頁碼（重設為 1）
  - 搜尋參數
  - 更新搜尋歷史
  - 更新熱門搜尋統計
- **功能**: 執行完整的搜尋邏輯

#### 8. `display_search_history`
- **觸發**: `search-history-store.data` 更新
- **輸出**: 歷史列表組件
- **功能**: 顯示最近 5 次搜尋

#### 9. `display_popular_searches`
- **觸發**: `popular-searches-store.data` 更新
- **輸出**: 熱門列表組件
- **功能**: 顯示前 5 個熱門搜尋

#### 10. `replay_history_search`
- **觸發**: 點擊歷史項目（Pattern Matching）
- **輸出**: 填入關鍵字、觸發搜尋
- **功能**: 重新執行歷史搜尋

#### 11. `search_popular_term`
- **觸發**: 點擊熱門項目（Pattern Matching）
- **輸出**: 填入關鍵字、觸發搜尋
- **功能**: 執行熱門搜尋

#### 12. `trigger_live_search` (可選)
- **觸發**: 關鍵字、料理、評分改變
- **輸出**: 觸發搜尋
- **功能**: 即時搜尋（無需點擊按鈕）

#### 13. `toggle_search_sidebar`
- **觸發**: 關鍵字輸入、頁面模式
- **輸出**: 側邊欄顯示狀態
- **功能**: 在首頁顯示歷史和熱門

---

## State Management

### dcc.Store 組件設計

#### 1. `search-history-store`
- **Storage Type**: `session`
- **用途**: 儲存搜尋歷史
- **數據結構**:
```python
[
    {
        'query': '關鍵字',
        'filters': {
            'cuisine': '料理類型',
            'rating': 評分,
            'price': ['budget', 'mid'],
            'stations': ['Kyoto', 'Sanjo'],
            'min_reviews': 50
        },
        'timestamp': '2025-11-05 14:30:00'
    },
    ...
]
```
- **最大筆數**: 10 筆

#### 2. `search-suggestions-store`
- **Storage Type**: `memory`
- **用途**: 暫存即時搜尋建議
- **數據結構**:
```python
[
    {
        'text': '建議文字',
        'category': '類別說明',
        'icon': 'fa-icon-name',
        'type': 'restaurant/cuisine/station',
        'value': '實際值'
    },
    ...
]
```

#### 3. `active-filters-store`
- **Storage Type**: `memory`
- **用途**: 記錄當前活躍的篩選器
- **數據結構**:
```python
{
    'keyword': '搜尋關鍵字',
    'cuisine': '料理類型',
    'rating': 4,
    'price_filters': ['budget', 'mid'],
    'stations': ['Kyoto', 'Sanjo'],
    'min_reviews': 50,
    'sort_by': 'rating_desc'
}
```

#### 4. `popular-searches-store`
- **Storage Type**: `local`
- **用途**: 長期儲存熱門搜尋統計
- **數據結構**:
```python
{
    'query:sushi': {
        'term': 'sushi',
        'type': 'query',
        'count': 42
    },
    'cuisine:Ramen': {
        'term': 'Ramen',
        'type': 'cuisine',
        'count': 38
    },
    ...
}
```

#### 5. `search-trigger`
- **Storage Type**: `memory`
- **用途**: 觸發搜尋的信號
- **數據結構**: `timestamp` (float)

#### 6. `filters-open-state`
- **Storage Type**: `memory`
- **用途**: 記錄進階篩選器開關狀態
- **數據結構**: `True` / `False`

---

## 使用範例

### 範例 1: 基本關鍵字搜尋

```python
# 使用者輸入 "sushi"
# → update_search_suggestions 顯示建議
# → 使用者按下搜尋
# → handle_comprehensive_search 執行
# → 返回所有包含 "sushi" 的餐廳
```

### 範例 2: 組合篩選

```python
# 使用者設定:
# - 關鍵字: "ramen"
# - 料理類型: "Ramen"
# - 評分: 4+ 星
# - 價格: Budget, Mid-range
# - 地點: Kyoto Station
# - 最少評論: 50+
# - 排序: 評分高到低

# → handle_comprehensive_search 依序應用所有篩選器
# → 返回符合所有條件的餐廳列表
```

### 範例 3: 使用搜尋歷史

```python
# 使用者點擊歷史項目 "kaiseki"
# → replay_history_search 被觸發
# → 填入關鍵字並觸發搜尋
# → handle_comprehensive_search 執行
```

### 範例 4: 移除篩選標籤

```python
# 顯示的篩選標籤:
# [Cuisine: Sushi] [Rating: ⭐⭐⭐⭐+] [Budget] [Location: Kyoto]
#
# 使用者點擊 [Budget] 的 X 按鈕
# → remove_filter_chip 被觸發
# → price-filter.value 更新（移除 'budget'）
# → update_filter_chips 重新生成標籤
```

---

## 樣式客製化

### 修改顏色主題

在 `enhanced_search_styles.css` 中修改以下變數：

```css
/* 金色強調色 */
#deb522 → 您的主色

/* 深色背景 */
rgba(26, 26, 26, 0.95) → 您的背景色

/* Hover 效果 */
rgba(222, 181, 34, 0.1) → 您的 hover 色
```

### 修改建議框樣式

```css
.suggestions-dropdown {
    max-height: 400px;  /* 調整最大高度 */
    border-radius: 12px; /* 調整圓角 */
}
```

### 修改篩選器布局

```css
.advanced-filters-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    /* 調整為固定 2 欄 */
    grid-template-columns: repeat(2, 1fr);
}
```

### 響應式斷點

```css
@media (max-width: 1024px) {
    /* 平板樣式 */
}

@media (max-width: 768px) {
    /* 手機樣式 */
}
```

---

## 疑難排解

### 問題 1: 搜尋建議不顯示

**可能原因**:
- 關鍵字少於 2 個字元
- `restaurants_df` 未正確傳入

**解決方法**:
```python
# 檢查 DataFrame 是否正確載入
print(restaurants_df.head())
print(restaurants_df.columns)

# 檢查搜尋函數
suggestions = generate_search_suggestions('test', restaurants_df)
print(suggestions)
```

### 問題 2: 篩選器不生效

**可能原因**:
- Callback 未正確註冊
- Store 組件未添加到 layout

**解決方法**:
```python
# 確認 Callbacks 已註冊
register_search_callbacks(app, restaurants_df)

# 確認 Stores 已添加
create_search_stores()  # 在 app.layout 中
```

### 問題 3: 樣式未正確顯示

**可能原因**:
- CSS 檔案未正確載入
- 快取問題

**解決方法**:
```python
# 清除瀏覽器快取 (Ctrl + Shift + R)
# 或在 app 初始化時添加:
app.config.suppress_callback_exceptions = True
app.config.update({'serve_locally': True})
```

### 問題 4: Pattern Matching Callbacks 錯誤

**可能原因**:
- Dash 版本過舊（需 2.0+）
- 組件 ID 格式錯誤

**解決方法**:
```bash
# 升級 Dash
pip install --upgrade dash

# 檢查組件 ID 格式
id={'type': 'remove-filter', 'filter': filter_type, 'value': value}
```

### 問題 5: 搜尋歷史未保存

**可能原因**:
- Storage type 設定錯誤
- 瀏覽器不支援 sessionStorage

**解決方法**:
```python
# 檢查 Store 設定
dcc.Store(id='search-history-store', storage_type='session')

# 測試 Storage
print("History:", history)
```

---

## 進階優化建議

### 1. 模糊搜尋 (Fuzzy Search)

安裝 `fuzzywuzzy`:
```bash
pip install fuzzywuzzy python-Levenshtein
```

在 `generate_search_suggestions` 中添加:
```python
from fuzzywuzzy import fuzz

# 計算相似度
similarity = fuzz.ratio(keyword.lower(), restaurant_name.lower())
if similarity > 80:  # 80% 相似度以上
    suggestions.append(...)
```

### 2. 搜尋結果高亮

修改 `create_destination_card` 函數:
```python
def highlight_keyword(text, keyword):
    if not keyword:
        return text
    pattern = re.compile(f'({re.escape(keyword)})', re.IGNORECASE)
    return pattern.sub(r'<mark>\1</mark>', text)
```

### 3. 無限滾動 (Infinite Scroll)

使用 `dcc.Interval` 或 JavaScript callback:
```python
@app.callback(
    Output('restaurant-grid', 'children', allow_duplicate=True),
    [Input('scroll-trigger', 'data')],
    [State('current-page-store', 'data')],
    prevent_initial_call=True
)
def load_more_restaurants(trigger, current_page):
    # 載入下一頁資料
    ...
```

### 4. 搜尋建議快取

使用 `@lru_cache` 減少重複計算:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def generate_search_suggestions_cached(keyword, df_id):
    # df_id = hash(restaurants_df)
    return generate_search_suggestions(keyword, restaurants_df)
```

### 5. 分析與追蹤

記錄搜尋行為到資料庫:
```python
def log_search_event(user_id, keyword, filters, result_count):
    # 寫入資料庫或 Analytics
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO search_logs VALUES (?, ?, ?, ?, ?)",
        (user_id, keyword, str(filters), result_count, datetime.now())
    )
    conn.commit()
```

---

## 測試清單

在部署前，請確認以下功能正常：

- [ ] 關鍵字輸入顯示建議
- [ ] 點擊建議項目填入搜尋框
- [ ] 進階篩選器展開/收合
- [ ] 所有篩選器正確過濾結果
- [ ] 篩選標籤正確顯示
- [ ] 可移除單個篩選標籤
- [ ] 清除全部篩選器功能
- [ ] 搜尋結果正確排序
- [ ] 搜尋歷史記錄正確
- [ ] 點擊歷史可重新搜尋
- [ ] 熱門搜尋統計正確
- [ ] 點擊熱門項目可搜尋
- [ ] 響應式設計在手機正常
- [ ] 無障礙功能（鍵盤導航）

---

## 聯絡與支援

如有問題或建議，請查閱:
- `CLAUDE.md`: 專案整體說明
- `app.py`: 主應用程式
- `components/enhanced_search.py`: 組件定義
- `callbacks/search_callbacks.py`: Callback 邏輯

---

**最後更新**: 2025-11-05
**版本**: 1.0.0
**作者**: Claude (Anthropic)
