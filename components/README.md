# Enhanced Search Components
# 增強搜尋組件說明

本目錄包含 Voyage 餐廳搜尋應用的增強搜尋系統組件。

---

## 📁 檔案結構

```
components/
└── enhanced_search.py          # 搜尋組件與輔助函數
└── README.md                   # 本文件
```

---

## 🎯 核心功能

### 1. UI 組件

#### `create_enhanced_search_bar(restaurants_df)`
創建完整的增強搜尋欄，包含：
- 關鍵字輸入框（with debounce）
- 料理類型下拉選單
- 評分篩選器
- 進階篩選按鈕
- 搜尋按鈕

**使用範例**:
```python
from components.enhanced_search import create_enhanced_search_bar
import pandas as pd

restaurants_df = pd.read_csv('data/Kyoto_Restaurant_Info_Full.csv')
search_bar = create_enhanced_search_bar(restaurants_df)
```

#### `create_search_stores()`
創建所有搜尋相關的 dcc.Store 組件：
- `search-history-store`: 搜尋歷史（session storage）
- `search-suggestions-store`: 即時建議（memory）
- `active-filters-store`: 活躍篩選器（memory）
- `popular-searches-store`: 熱門搜尋（local storage）
- `search-trigger`: 搜尋觸發器（memory）
- `filters-open-state`: 篩選器狀態（memory）

**使用範例**:
```python
from components.enhanced_search import create_search_stores

app.layout = html.Div([
    create_search_stores(),
    # ... 其他組件
])
```

### 2. 輔助組件

#### `create_suggestion_item(text, category, icon)`
創建單個搜尋建議項目

**參數**:
- `text`: 顯示文字
- `category`: 類別說明
- `icon`: FontAwesome icon class

**使用範例**:
```python
suggestion = create_suggestion_item(
    text='Sushi Kyoto',
    category='Japanese · Kyoto Station',
    icon='fa-store'
)
```

#### `create_filter_chip(label, value, filter_type)`
創建篩選標籤（可移除）

**參數**:
- `label`: 顯示文字
- `value`: 實際值
- `filter_type`: 篩選器類型（'cuisine', 'rating', 'price', 'station', 'reviews'）

**使用範例**:
```python
chip = create_filter_chip(
    label='Cuisine: Sushi',
    value='Sushi',
    filter_type='cuisine'
)
```

#### `create_history_item(query, timestamp)`
創建搜尋歷史項目

#### `create_popular_item(label, count)`
創建熱門搜尋項目

---

## 🔧 核心函數

### 搜尋與篩選

#### `generate_search_suggestions(keyword, restaurants_df, max_results=8)`
生成即時搜尋建議

**邏輯**:
1. 搜尋餐廳名稱（max 3）
2. 搜尋料理類型（max 3）
3. 搜尋車站地點（max 2）
4. 合併並返回最多 8 個建議

**返回格式**:
```python
[
    {
        'text': '建議文字',
        'category': '類別說明',
        'icon': 'fa-icon',
        'type': 'restaurant|cuisine|station',
        'value': '實際值'
    },
    ...
]
```

**使用範例**:
```python
suggestions = generate_search_suggestions('sushi', restaurants_df)
for sugg in suggestions:
    print(f"{sugg['text']} - {sugg['category']}")
```

#### `apply_advanced_filters(df, price_filters, stations, min_reviews, sort_by)`
應用進階篩選器

**參數**:
- `df`: 餐廳 DataFrame
- `price_filters`: list of 'budget', 'mid', 'high'
- `stations`: list of station names
- `min_reviews`: int, 最少評論數
- `sort_by`: 'rating_desc', 'rating_asc', 'reviews', 'name'

**返回**: 篩選和排序後的 DataFrame

**使用範例**:
```python
filtered_df = apply_advanced_filters(
    df=restaurants_df,
    price_filters=['budget', 'mid'],
    stations=['Kyoto', 'Sanjo'],
    min_reviews=50,
    sort_by='rating_desc'
)
```

#### `get_price_category(price_str)`
從價格字串判斷價格類別

**輸入**: `"¥2000~¥2999"`
**輸出**: `"mid"`

**分類規則**:
- `budget`: ¥1000-¥1999
- `mid`: ¥2000-¥3999
- `high`: ¥4000+

### 歷史與統計

#### `add_to_search_history(history, query, filters)`
添加搜尋記錄到歷史

**參數**:
- `history`: 現有歷史 list
- `query`: 搜尋關鍵字
- `filters`: 篩選器 dict

**返回**: 更新後的歷史 list（最多 10 筆）

**使用範例**:
```python
history = []
history = add_to_search_history(
    history,
    query='sushi',
    filters={'cuisine': 'Sushi', 'rating': 4}
)
```

#### `update_popular_searches(popular_dict, search_term, search_type)`
更新熱門搜尋統計

**參數**:
- `popular_dict`: 現有統計 dict
- `search_term`: 搜尋詞
- `search_type`: 'query', 'cuisine', 'station'

**返回**: 更新後的統計 dict

**使用範例**:
```python
popular = {}
popular = update_popular_searches(popular, 'sushi', 'query')
popular = update_popular_searches(popular, 'Ramen', 'cuisine')
```

#### `get_top_popular_searches(popular_dict, top_n=5)`
獲取最熱門的搜尋詞

**返回**: List of tuples `[(term, count), ...]`

**使用範例**:
```python
top_searches = get_top_popular_searches(popular_dict, top_n=5)
for term, count in top_searches:
    print(f"{term}: {count} searches")
```

---

## 🎨 樣式

所有組件使用的 CSS class 定義在 `assets/enhanced_search_styles.css`。

### 主要 CSS Classes

- `.search-container`: 搜尋欄容器
- `.search-input-group`: 輸入框組
- `.suggestions-dropdown`: 建議下拉框
- `.suggestion-item`: 單個建議項目
- `.advanced-filters-container`: 進階篩選器容器
- `.filter-chip`: 篩選標籤
- `.history-item`: 歷史項目
- `.popular-item`: 熱門項目

---

## 📊 數據結構

### 搜尋歷史 (search-history-store)

```python
[
    {
        'query': '關鍵字',
        'filters': {
            'cuisine': '料理類型',
            'rating': 4,
            'price': ['budget', 'mid'],
            'stations': ['Kyoto', 'Sanjo'],
            'min_reviews': 50
        },
        'timestamp': '2025-11-05 14:30:00'
    },
    ...
]
```

### 熱門搜尋 (popular-searches-store)

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

### 活躍篩選器 (active-filters-store)

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

---

## 🔌 與 Callbacks 整合

組件需要配合 `callbacks/search_callbacks.py` 中的 callbacks 使用。

**註冊方式**:
```python
from callbacks.search_callbacks import register_search_callbacks

register_search_callbacks(app, restaurants_df)
```

詳細的 callback 說明請參考 `SEARCH_ARCHITECTURE.md`。

---

## 🧪 測試

使用 `test_enhanced_search.py` 進行獨立測試：

```bash
python test_enhanced_search.py
```

然後訪問 http://127.0.0.1:8050 進行功能測試。

---

## 📖 相關文件

- **整合指南**: `ENHANCED_SEARCH_INTEGRATION.md`
- **架構說明**: `SEARCH_ARCHITECTURE.md`
- **整合檢查清單**: `INTEGRATION_CHECKLIST.md`
- **Callbacks 說明**: `callbacks/search_callbacks.py`

---

## 🛠️ 技術細節

### 依賴套件

- `dash`: Dash 框架
- `dash-bootstrap-components`: Bootstrap 組件
- `pandas`: 資料處理

### 瀏覽器支援

- Chrome/Edge (Chromium) 90+
- Firefox 88+
- Safari 14+
- iOS Safari 14+
- Android Chrome 90+

### 效能考量

- **Debouncing**: 輸入框使用 300ms debounce
- **建議數量限制**: 最多 8 個建議
- **歷史記錄限制**: 最多 10 筆
- **分頁**: 搜尋結果每頁 15 筆

---

## 🔧 客製化

### 修改建議數量

在 `generate_search_suggestions()` 中修改 `max_results` 參數：

```python
suggestions = generate_search_suggestions(keyword, df, max_results=10)
```

### 修改歷史記錄數量

在 `add_to_search_history()` 中修改：

```python
return history[:20]  # 改為 20 筆
```

### 修改價格分類

在 `get_price_category()` 中修改邏輯：

```python
if '¥1500' in price_str or '¥2499' in price_str:
    return 'budget'
# ... 自訂分類
```

---

## 🐛 常見問題

### Q: 建議不顯示？
A: 確認關鍵字長度 >= 2 且 `restaurants_df` 正確傳入。

### Q: 篩選器不生效？
A: 確認 callbacks 已註冊且 Store 組件已添加到 layout。

### Q: 樣式不正確？
A: 確認 `enhanced_search_styles.css` 已添加到 external_stylesheets。

### Q: Pattern Matching 錯誤？
A: 確認 Dash 版本 >= 2.0。

---

## 📄 授權

此組件為 Voyage 專案的一部分，遵循專案授權協議。

---

## 👤 維護者

**Claude (Anthropic)**
- 創建日期: 2025-11-05
- 版本: 1.0.0

---

## 🔄 更新紀錄

### v1.0.0 (2025-11-05)
- 初始版本
- 實作即時搜尋建議
- 實作進階篩選器
- 實作搜尋歷史與熱門搜尋
- 實作篩選標籤管理

---

**需要幫助？** 請參考完整文件或聯繫維護者。
