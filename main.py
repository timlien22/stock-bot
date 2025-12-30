import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 🟢 【設定區】
target_stocks = ['2317.TW', '2645.TW', '2382.TW', '0050.TW']

print(f"🚀 啟動 V3.0 究極診斷 (布林通道 + AI戰略)...\n")

for stock_id in target_stocks:
    try:
        # 下載資料
        df = yf.download(stock_id, period="150d", interval="1d", progress=False, multi_level_index=False)
        if len(df) < 60: continue

        # 1. 計算指標 (同步 Dashboard 邏輯)
        df.ta.kdj(length=9, signal=3, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.sma(length=20, append=True) # 月線
        
        # 布林通道 (長度20, 標準差2)
        # 欄位會自動生成: BBL_20_2.0 (下), BBM_20_2.0 (中), BBU_20_2.0 (上)
        df.ta.bbands(length=20, std=2, append=True)
        
        # 乖離率
        df['Bias_20'] = ((df['Close'] - df['SMA_20']) / df['SMA_20']) * 100

        # 2. 數據提取
        price = df['Close'].iloc[-1]
        ma20 = df['SMA_20'].iloc[-1]
        bias = df['Bias_20'].iloc[-1]
        
        j_cur = df['J_9_3'].iloc[-1]
        j_prev = df['J_9_3'].iloc[-2]
        j_prev2 = df['J_9_3'].iloc[-3]
        
        bb_lower = df['BBL_20_2.0'].iloc[-1]
        bb_upper = df['BBU_20_2.0'].iloc[-1]
        
        vol_cur = df['Volume'].iloc[-1]
        vol_avg = df['Volume'].tail(10).mean()

        # 3. 戰略判定 (AI Logic)
        print(f"📊 [{stock_id}] 現價 {price:.2f} | 乖離率 {bias:.1f}%")
        
        # 情境 A: 順勢多頭
        if price > ma20:
            if j_cur > 80:
                print(f"   ⚠️ [過熱] 雖在多頭，但 J值({j_cur:.1f}) 過高，且接近布林上軌 ({bb_upper:.1f})。")
            else:
                print(f"   🚀 [順勢] 站穩月線 + 趨勢向上。")
                if vol_cur > vol_avg: print("      ╰─ 🔥 攻擊量能出現！")
        
        # 情境 B: 跌深反彈
        elif price < ma20:
            # 判斷反彈條件
            is_hook = (j_prev2 > j_prev) and (j_cur > j_prev)
            is_deep = bias < -5
            is_floor = price <= bb_lower * 1.02 # 接近下軌
            
            if is_hook and (is_deep or is_floor):
                print(f"   🎣 [搶反彈] 觸發！負乖離過大 + J線勾頭。")
                print(f"      ╰─ 地板支撐: 布林下軌 {bb_lower:.2f} (目前 {price:.2f})")
            else:
                print(f"   🥶 [空頭] 弱勢整理中，還沒止跌。")
        
        # 顯示 J 線路徑
        print(f"   🌊 J線動態: {j_prev2:.1f} ➔ {j_prev:.1f} ➔ {j_cur:.1f}")
        print("-" * 40)

    except Exception as e:
        print(f"[{stock_id}] 錯誤: {e}")