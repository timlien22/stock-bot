import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 🟢 【設定區】 掃描清單
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

print(f"📡 V3.0 雙模式雷達啟動... 掃描 {len(scan_list)} 檔")
print("🎯 目標：1.順勢攻擊股  2.布林跌深反彈股\n")
print("-" * 60)

found_targets = []

for stock_id in scan_list:
    try:
        df = yf.download(stock_id, period="100d", interval="1d", progress=False, multi_level_index=False)
        if len(df) < 60: continue
        
        # 計算指標
        df.ta.kdj(length=9, signal=3, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df['Bias_20'] = ((df['Close'] - df['SMA_20']) / df['SMA_20']) * 100

        # 數據提取
        price = df['Close'].iloc[-1]
        ma20 = df['SMA_20'].iloc[-1]
        bias = df['Bias_20'].iloc[-1]
        
        j_cur = df['J_9_3'].iloc[-1]
        j_prev = df['J_9_3'].iloc[-2]
        j_prev2 = df['J_9_3'].iloc[-3]
        
        bb_lower = df['BBL_20_2.0'].iloc[-1]
        vol_cur = df['Volume'].iloc[-1]
        vol_avg = df['Volume'].tail(10).mean()

        # === 雙模式判斷 ===
        
        mode = None
        
        # 模式 1: 順勢攻擊 (站上月線 + J線低檔勾起 或 MACD強 + 有量)
        if price > ma20:
            is_hook = (j_prev2 > j_prev) and (j_cur > j_prev)
            is_vol = vol_cur > vol_avg
            if is_hook and is_vol and j_cur < 80:
                mode = "🚀 [順勢攻擊]"
        
        # 模式 2: 跌深反彈 (跌破月線 + 負乖離大 + 觸及布林下軌 + 勾頭)
        elif price < ma20:
            is_hook = (j_prev2 > j_prev) and (j_cur > j_prev)
            is_deep = bias < -5
            is_floor = price <= bb_lower * 1.02
            if is_hook and (is_deep or is_floor):
                mode = "🎣 [跌深反彈]"

        # === 輸出結果 ===
        if mode:
            print(f"{mode} {stock_id} | 現價 {price:.2f}")
            print(f"   ├─ 乖離率: {bias:.1f}%")
            print(f"   ├─ J線: {j_prev:.1f} ➔ {j_cur:.1f}")
            print(f"   └─ 量能: {vol_cur/vol_avg:.1f} 倍")
            print("-" * 30)
            found_targets.append(stock_id)

    except:
        pass

print(f"\n✅ 掃描完畢。發現 {len(found_targets)} 檔機會股。")