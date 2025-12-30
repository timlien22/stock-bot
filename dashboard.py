import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- 網頁設定 ---
st.set_page_config(page_title="股市自幹戰情室 Ultimate", page_icon="⚡", layout="wide")

# --- 股市術語資料庫 ---
STOCK_TERMS = {
    "存股": "買進股票後，長期持有數年不賣出，以每年領股利為主的一種股票投資法。",
    "分散風險": "將資金分配在多種資產上，回報率關聯性低，降低風險且不損及收益。",
    "融資": "向券商借錢買股票。融資餘額增加通常代表散戶進場，籌碼凌亂。",
    "融券": "向券商借股票來賣（看空）。之後再買回還給券商。",
    "解套": "買入股票套牢後，股價回升至原來買進價位。",
    "買超/賣超": "買進/賣出的數量大於另一方。外資買超通常被視為利多。",
    "多頭 (牛市)": "預期股價上漲，大漲小跌，均線向上排列。",
    "空頭 (熊市)": "預期股價下跌，大跌小漲，均線向下壓制。",
    "軋空": "做空者（融券）因股價不跌反漲，被迫高價買回股票，導致股價更急漲。",
    "跳空": "開盤價直接高於昨收（跳空漲）或低於昨收（跳空跌），中間沒有成交價格。",
    "本益比 (PE)": "股價 / EPS。用來衡量股價貴不貴，越低通常越便宜（但也可能是有雷）。",
    "EPS (每股盈餘)": "公司賺的錢除以股數。代表每一股幫您賺多少錢。",
    "乖離率 (Bias)": "股價與均線的距離。(股價-均線)/均線。正乖離過大易拉回，負乖離過大易反彈。",
    "布林通道": "由中軌(月線)、上軌(壓力)、下軌(支撐)組成的帶狀區域。股價碰到下軌易反彈，碰上軌易回檔。",
    "MACD": "判斷中長期趨勢。紅柱代表多頭動能，綠柱代表空頭動能。紅柱縮短代表漲勢趨緩。",
    "KD指標": "判斷超買超賣。K>80過熱，K<20超賣。黃金交叉買進，死亡交叉賣出。",
    "三大法人": "外資（外國錢）、投信（基金公司）、自營商（券商自己）。",
    "量縮": "成交量變少。下跌量縮代表賣壓減輕（好事），上漲量縮代表沒人追價（壞事）。",
}

# --- 資料取得與精密計算 ---
def get_stock_data(ticker):
    try:
        df = yf.download(ticker, period="150d", interval="1d", progress=False, multi_level_index=False)
        if len(df) < 60: return None
        
        # 1. 基礎指標
        df.ta.kdj(length=9, signal=3, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.sma(length=20, append=True) # 月線
        
        # 2. 精密指標：布林通道 (防呆寫法)
        bb_df = df.ta.bbands(length=20, std=2)
        df = pd.concat([df, bb_df], axis=1)
        
        # 3. 乖離率 (Bias)
        df['Bias_20'] = ((df['Close'] - df['SMA_20']) / df['SMA_20']) * 100
        
        return df
    except:
        return None

# --- AI 戰略分析引擎 (核心升級 V4.0) ---
def analyze_strategy(df):
    report = {
        "mode": "觀察中", 
        "color": "gray",
        "reasons": [],
        "risks": []
    }
    
    # 提取數據
    price = df['Close'].iloc[-1]
    ma20 = df['SMA_20'].iloc[-1]
    bias = df['Bias_20'].iloc[-1]
    j_cur = df['J_9_3'].iloc[-1]
    j_prev = df['J_9_3'].iloc[-2]
    j_prev2 = df['J_9_3'].iloc[-3]
    vol_cur = df['Volume'].iloc[-1]
    vol_avg = df['Volume'].tail(10).mean()
    
    # 智慧搜尋欄位 (防呆)
    col_bbl = [c for c in df.columns if c.startswith('BBL')][0]
    col_bbu = [c for c in df.columns if c.startswith('BBU')][0]
    # MACD 柱狀圖通常叫做 MACDh_12_26_9
    col_macdh = [c for c in df.columns if c.startswith('MACDh')][0]
    
    bb_lower = df[col_bbl].iloc[-1]
    bb_upper = df[col_bbu].iloc[-1]
    macd_hist_cur = df[col_macdh].iloc[-1]
    macd_hist_prev = df[col_macdh].iloc[-2]

    # --- 戰略判定邏輯 ---
    
    # 情境 1: 順勢多頭
    if price > ma20:
        if j_cur > 80:
            report["mode"] = "⚠️ 多頭過熱 (小心回檔)"
            report["color"] = "orange"
            report["risks"].append(f"J值 {j_cur:.1f} 過熱，雖在多頭但不宜追高。")
            if macd_hist_cur < macd_hist_prev and macd_hist_cur > 0:
                 report["risks"].append("⚠️ 注意：MACD 紅柱正在縮短！買盤力道減弱中。")
        else:
            report["mode"] = "🚀 順勢多頭 (持有/加碼)"
            report["color"] = "green"
            report["reasons"].append("股價穩站月線 (生命線) 之上，趨勢向上。")
            
            # 檢查動能背離
            if macd_hist_cur < macd_hist_prev and macd_hist_cur > 0:
                 report["risks"].append("雖是多頭，但 MACD 紅柱變短 (漲勢趨緩)，高檔請勿過度追價。")

    # 情境 2: 跌深反彈
    elif price < ma20:
        is_hook = (j_prev2 > j_prev) and (j_cur > j_prev)
        is_deep = bias < -5
        is_floor = price <= bb_lower * 1.02
        
        if is_hook and (is_deep or is_floor):
            report["mode"] = "🎣 跌深反彈 (搶短線)"
            report["color"] = "blue"
            report["reasons"].append(f"負乖離過大 ({bias:.1f}%) + 觸及布林下軌。")
            
            # 檢查 MACD 是否綠柱收斂 (好事)
            if macd_hist_cur > macd_hist_prev and macd_hist_cur < 0:
                report["reasons"].append("MACD 綠柱縮短，賣壓減輕，有利反彈。")
        else:
            report["mode"] = "🥶 空頭弱勢 (觀望)"
            report["color"] = "red"
            report["risks"].append("股價被月線壓著打，且無明顯反轉訊號。")

    return report, col_bbl, col_bbu, col_macdh # 回傳 macd 欄位名稱

# --- 側邊欄 ---
st.sidebar.title("🎛️ 戰情室控制台")
tab1, tab2, tab3 = st.tabs(["🔍 精密診斷 (Pro)", "📡 策略掃描", "📖 股市辭典"])

# ==========================================
# Tab 1: 精密診斷
# ==========================================
with tab1:
    st.header("🔍 個股精密戰略分析")
    default_stocks = "2317.TW, 2645.TW, 2882.TW, 0050.TW"
    user_input = st.text_input("輸入代號", default_stocks)
    stock_list = [x.strip() for x in user_input.split(',')]
    
    if st.button("開始分析", key="btn_pro"):
        for stock_id in stock_list:
            df = get_stock_data(stock_id)
            if df is None:
                st.error(f"❌ {stock_id} 讀取失敗")
                continue
            
            # 執行戰略分析
            analysis, col_bbl, col_bbu, col_macdh = analyze_strategy(df)
            price = df['Close'].iloc[-1]
            change = price - df['Close'].iloc[-2]
            
            with st.container():
                c1, c2 = st.columns([3, 7])
                c1.subheader(f"📊 {stock_id}")
                c1.metric("現價", f"{price:.2f}", f"{change:.2f}")
                
                with c2:
                    st.markdown(f"### 戰略模式：:{analysis['color']}[{analysis['mode']}]")
                    with st.expander("查看詳細分析理由", expanded=True):
                        if analysis['reasons']:
                            st.markdown("**✅ 有利因素：**")
                            for r in analysis['reasons']: st.info(r)
                        if analysis['risks']:
                            st.markdown("**⚠️ 風險提示：**")
                            for r in analysis['risks']: st.warning(r)

                # 圖表 1: 布林通道
                st.caption("📈 主圖：股價(藍) vs 布林通道(灰)")
                chart_data = pd.DataFrame({
                    '股價': df['Close'],
                    '月線': df['SMA_20'],
                    '上軌': df[col_bbu],
                    '下軌': df[col_bbl]
                }).tail(60)
                st.line_chart(chart_data, color=["#0000FF", "#FFA500", "#A9A9A9", "#A9A9A9"])
                
                # 圖表 2: MACD 柱狀圖 (新增!)
                st.caption("📊 副圖 1：MACD 能量柱 (紅柱=多頭, 綠柱=空頭)")
                # 為了讓柱狀圖更明顯，我們只畫柱狀部分
                st.bar_chart(df[col_macdh].tail(60))

                # 圖表 3: J線
                st.caption("🌊 副圖 2：J 線動能 (高檔鈍化 vs 勾頭向下)")
                st.line_chart(df['J_9_3'].tail(60), color="#FF0000")

                st.divider()

# ==========================================
# Tab 2: 策略掃描
# ==========================================
with tab2:
    st.header("📡 雙模式雷達：順勢 vs 反彈")
    targets = [
        '2330.TW', '2317.TW', '2454.TW', '2303.TW', '2881.TW', '2308.TW', '2882.TW', '2891.TW', 
        '2002.TW', '2412.TW', '2886.TW', '2884.TW', '1216.TW', '2892.TW', '5880.TW', '2885.TW',
        '2382.TW', '2301.TW', '2880.TW', '3711.TW', '2345.TW', '2883.TW', '2887.TW', '1101.TW', 
        '5876.TW', '2357.TW', '2890.TW', '2327.TW', '3008.TW', '2207.TW', '2379.TW', '2395.TW', 
        '3045.TW', '5871.TW', '2912.TW', '2603.TW', '1303.TW', '1301.TW', '2353.TW', '4938.TW', 
        '1326.TW', '1402.TW', '2801.TW', '2105.TW', '1102.TW', '2408.TW', '9910.TW', '2354.TW',
        '6669.TW', '3037.TW', '2645.TW', '0050.TW'
    ]
    scan_list = list(set(targets))

    if st.button("🚀 啟動雙模式雷達"):
        progress_bar = st.progress(0)
        results = []
        
        for i, stock_id in enumerate(scan_list):
            progress_bar.progress((i + 1) / len(scan_list))
            df = get_stock_data(stock_id)
            if df is None: continue
            
            # 使用跟 Tab 1 一樣的分析邏輯
            analysis, _, _, _ = analyze_strategy(df)
            
            if "多頭" in analysis['mode'] or "反彈" in analysis['mode']:
                price = df['Close'].iloc[-1]
                vol_cur = df['Volume'].iloc[-1]
                vol_avg = df['Volume'].tail(10).mean()
                
                results.append({
                    "代號": stock_id,
                    "現價": f"{price:.2f}",
                    "戰略模式": analysis['mode'],
                    "量能倍數": f"{vol_cur/vol_avg:.1f} 倍"
                })
        
        progress_bar.empty()
        
        if results:
            st.success(f"掃描完成！共發現 {len(results)} 檔機會股")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("今日無明顯機會。")

# ==========================================
# Tab 3: 股市辭典
# ==========================================
with tab3:
    st.header("📖 股市術語大全")
    search_term = st.text_input("🔍 搜尋術語", "")
    for term, definition in STOCK_TERMS.items():
        if search_term in term or search_term in definition:
            with st.expander(f"📌 {term}"):
                st.write(definition)
