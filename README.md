# NASDAQ-100 H4CK3R DASHBOARD

![Python](https://img.shields.io/badge/Python-3.8%2B-00ff41?style=flat&logo=python&logoColor=00ff41&labelColor=0a0a0a&color=00ff41)
![Tkinter](https://img.shields.io/badge/Tkinter-✓-00ff41?style=flat&labelColor=0a0a0a&color=00ff41)
![yfinance](https://img.shields.io/badge/yfinance-✓-00ff41?style=flat&labelColor=0a0a0a&color=00ff41)
![matplotlib](https://img.shields.io/badge/matplotlib-✓-00ff41?style=flat&labelColor=0a0a0a&color=00ff41)

一個專為**那斯達克 100 指數（^NDX）**設計的桌面看盤工具，具備暗黑駭客風格 UI、即時圖表、個股查詢、Watchlist、恐懼貪婪指數、技術指標警報與 DCA 定投回測等功能。

---

## 📸 功能一覽

| 功能 | 說明 |
|------|------|
| **NASDAQ-100 即時走勢圖** | 含成交量柱狀圖、SMA 均線（20/50/200）切換 |
| **左側資訊面板** | 股票查詢、13 項即時數據、1W 迷你圖、Watchlist、科技新聞 |
| **恐慌貪婪指數（F&G）** | 即時顯示市場情緒，附彩色進度條 |
| **SMA 均線警報** | 價格跌破 SMA50/SMA200 時自動提示加倉比例 |
| **F&G 極度恐慌警報** | 指數 < 20 時提示今日為定投加倉日 |
| **DCA 定投回測** | 輸入時間範圍與金額，模擬定期定額績效 |
| **拖曳式教學系統** | `?` 鍵叫出各區塊說明，可自由拖曳定位 |
| **6 套主題切換** | Ctrl+T 循環切換 H4CK3R / MATRIX / DRACULA / NORD / SOLARIZED / MONOKAI |
| **圖表區間選取** | 滑鼠拖曳選取範圍，即時顯示漲跌幅與價格變化 |

---

## 🚀 快速開始

### 需求

- Python 3.8+
- pip

### 安裝與執行

```bash
# 1. 克隆倉庫
git clone https://github.com/pouheng/nasdaq-tool.git
cd nasdaq-tool

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 啟動
python nasdaq_tool.py
```

也可直接雙擊 `run.bat`（會自動安裝依賴並啟動）。

如果遇到 PIL 相關錯誤：

```bash
pip install pillow
```

---

## 🎮 操作指南

### 🧰 左側面板

面板預設顯示在左側，佔約 20% 寬度：

- **拖曳邊界** — 可左右拖曳調整面板寬度
- **`[≡ HIDE]`** — 隱藏面板，按鈕變為 `[≡ PANEL]`，再按一次恢復

### 📊 NASDAQ-100 主圖

| 控制項 | 說明 |
|--------|------|
| `[panel]` | 切換左側面板 |
| `[AUTO OFF/ON]` | 每 60 秒自動刷新圖表與 F&G |
| 週期按鈕 | 1D / 5D / 1M / 3M / 6M / YTD / 1Y / 3Y / 5Y |
| SMA 按鈕 | 20（黃線月線）/ 50（青線季線）/ 200（紫紅線年線） |
| **圖表拖曳** | 按住左鍵拖曳選取區間，即時顯示 `$開盤 → $收盤 漲跌%` |
| `[DCA]` | 開啟定投回測 |

### 📈 SMA 技術指標

三條均線幫助判斷趨勢方向：

| 均線 | 顏色 | 週期 | 意義 |
|------|------|------|------|
| SMA20 | 黃 `#ffcc00` | 20 日（月線） | 短期爆發力與支撐 |
| SMA50 | 青 `#33ccff` | 50 日（季線） | 中期波段趨勢（主力生命線） |
| SMA200 | 紫紅 `#ff33cc` | 200 日（年線） | 牛熊分水嶺 |

**多頭排列：** SMA20 > SMA50 > SMA200，三線齊揚 → 順勢做多

**空頭排列：** SMA200 > SMA50 > SMA20，三線齊跌 → 保守觀望

**黃金交叉：** SMA20 由下往上突破 SMA50/SMA200 → 買進訊號

**死亡交叉：** SMA20 由上往下跌破 SMA50/SMA200 → 賣出訊號

### 🔔 自動警報

| 警報 | 觸發條件 | 顯示位置 |
|------|---------|---------|
| SMA 均線警報 | 價格跌破 SMA50 或 SMA200 | F&G 右側標籤（8 秒自動清除） |
| 恐慌加倉警報 | F&G < 20（極度恐慌） | F&G 右側標籤（8 秒自動清除） |

加倉比例計算方式：`偏離幅度 × 3`，SMA50 上限 20%，SMA200 上限 30%。

### 😨 恐慌貪婪指數（F&G）

資料來源：[Alternative.me Fear & Greed Index API](https://api.alternative.me/fng/)

| 數值範圍 | 情緒 | 顏色 | 建議 |
|---------|------|------|------|
| 0 — 25 | 極度恐慌 | 🔴 | 可能超賣，長期佈局機會 |
| 26 — 45 | 恐慌 | 🟠 | 觀望 |
| 46 — 55 | 中立 | 🟡 | 平穩 |
| 56 — 75 | 貪婪 | 🟢 | 樂觀 |
| 76 — 100 | 極度貪婪 | 💚 | 可能過熱，小心追高 |

### 📰 科技新聞

彙整 AAPL / MSFT / GOOGL / AMZN / NVDA / META / TSLA / AVGO 八檔科技股的最新新聞：

- 支援**滑鼠滾輪**滾動
- 點擊標題或縮圖可透過瀏覽器開啟全文
- 縮圖為懶加載，節省流量

### 💰 DCA 定投回測

按 toolbar 上的 `[DCA]` 按鈕開啟：

| 參數 | 說明 |
|------|------|
| 標的 | 預設 `^NDX`，可改為任何 yfinance 支援的代碼 |
| 開始 / 結束日期 | 輸入 `YYYY-MM-DD`，或按快速按鈕（1Y/3Y/5Y/MAX） |
| 頻率 | 週（每 5 交易日）/ 雙週（每 10 交易日）/ 月（每 21 交易日） |
| 每期金額 | 美元 USD |

結果會以獨立視窗顯示：

- **黃線** — 累計投入成本
- **綠線** — 資產價值成長曲線
- 下方統計：投入總額、市值、報酬率、累積股數

### ❓ 教學系統

按 `?` 鍵彈出各區塊的繁體中文教學提示，包含：

- NASDAQ-100 指數說明
- 圖表週期與 SMA 均線教學
- 恐慌貪婪指數用法
- 左側面板各區塊操作說明
- 自動刷新功能

**拖曳定位：** 按 `?` 開啟教學後，按 **F12** 進入拖曳模式，可自由拖曳每個提示視窗到想要的位置，再按一次 F12 儲存位置。位置會自動保存到 `help_positions.json`，重新啟動程式也會保留。

### 🎨 主題切換

按 **Ctrl+T** 循環切換 6 套主題：

| 主題 | 風格 |
|------|------|
| H4CK3R | 經典駭客綠黑 |
| MATRIX | 矩陣數字符號風格 |
| DRACULA | 暗紫紅對比 |
| NORD | 北歐冷色極簡 |
| SOLARIZED | 暖色護眼 |
| MONOKAI | 程式碼編輯器風格 |

---

## ⌨️ 快速鍵一覽

| 快捷鍵 | 功能 |
|--------|------|
| `Ctrl+T` | 循環切換主題 |
| `F12` | 教學模式下：切換拖曳定位模式 |
| `?` 按鈕 | 開關教學系統 |

---

## 📁 專案結構

```
NASDAQ tool/
├── nasdaq_tool.py      # 主程式
├── theme.py            # 6 套主題定義 + apply_theme()
├── requirements.txt    # Python 依賴
├── run.bat             # Windows 一鍵啟動腳本
├── help_positions.json # 教學視窗位置（執行時自動產生）
└── README.md           # 本文件
```

---

## 🔧 技術架構

| 層級 | 技術 |
|------|------|
| GUI | tkinter / ttk |
| 圖表 | matplotlib + FigureCanvasTkAgg |
| 資料源 | yfinance（Yahoo Finance） |
| 情緒指標 | alternative.me Fear & Greed API |
| 繪圖優化 | Pillow（PIL，新聞縮圖） |
| 主題系統 | 自定義 theme.py，支援 6 套配色 |

**資料來源聲明：** 本工具使用 **yfinance** 非官方 Yahoo Finance API 與 **alternative.me** 公開 API 取得資料。資料僅供參考，不構成投資建議。

---

## 📜 授權

MIT License
