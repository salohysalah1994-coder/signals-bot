import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timedelta

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="ماسح صفقات الفوركس الذكي - صلاح",
    page_icon="📈",
    layout="wide"
)

st.title("📈 روبوت الفوركس الذكي (سجل الصفقات المحدث) - صلاح")
st.markdown("البوت يقوم بمسح السوق وتحليل الشموع السابقة لعرض الفرص المتاحة.")
st.markdown("---")

# ==========================================
# 2. قائمة أزواج الفوركس وإعدادات الشريط الجانبي
# ==========================================
PAIRS_MAP = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "الذهب (XAU/USD)": "GC=F"
}

st.sidebar.header("⚙️ إعدادات سوق الفوركس")
st.sidebar.markdown(f"👤 **المتداول:** صلاح")
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني للفحص (الفريم):", ["1h", "30m", "15m", "5m"], index=0)

# ==========================================
# 3. دالة فحص السوق المبسطة والمضمنة
# ==========================================
def scan_market_signals():
    signals = []
    market_prices = []
    
    for name, symbol in PAIRS_MAP.items():
        try:
            # جلب البيانات بطريقة آمنة ومستقرة
            df = yf.download(symbol, period="5d", interval=TIMEFRAME, progress=False)
            if df.empty or len(df) < 50:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df.reset_index()
            time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
            df['datetime'] = pd.to_datetime(df[time_col])
            close_series = df['Close'].squeeze()
            
            # حفظ السعر الحالي للزوج لعرضه في لوحة الأسعار
            current_price = float(close_series.iloc[-1])
            market_prices.append({"الزوج": name, "السعر الحالي": round(current_price, 4)})
            
            # مؤشرات بسيطة وفعالة لاكتشاف التقاطع (SMA 5 & SMA 20)
            sma_fast = ta.sma(close_series, length=5)
            sma_slow = ta.sma(close_series, length=20)
            
            if sma_fast is None or sma_slow is None:
                continue
                
            # فحص آخر 10 شموع لتوليد إشارات واضحة
            last_24h_limit = datetime.now() - timedelta(hours=24)
            
            for i in range(25, len(df) - 1):
                candle_dt = df['datetime'].iloc[i]
                if candle_dt < last_24h_limit:
                    continue
                
                f_now, f_prev = sma_fast.iloc[i], sma_fast.iloc[i-1]
                s_now, s_prev = sma_slow.iloc[i], sma_slow.iloc[i-1]
                
                # شروط التقاطع الصعودي والهبوطي
                is_buy = (f_now > s_now) and (f_prev <= s_prev)
                is_sell = (f_now < s_now) and (f_prev >= s_prev)
                
                if is_buy:
                    signals.append({
                        "الوقت": str(candle_dt),
                        "الزوج": name,
                        "الإشارة": "🟢 صعود (شراء)",
                        "السعر عند الإشارة": round(float(close_series.iloc[i]), 4)
                    })
                elif is_sell:
                    signals.append({
                        "الوقت": str(candle_dt),
                        "الزوج": name,
                        "الإشارة": "🔴 هبوط (بيع)",
                        "السعر عند الإشارة": round(float(close_series.iloc[i]), 4)
                    })
        except Exception:
            continue
            
    return signals, market_prices

# ==========================================
# 4. العرض في واجهة Streamlit
# ==========================================
if st.button("🔄 فحص السوق وتحديث البيانات الآن"):
    st.rerun()

with st.spinner("جاري الاتصال بالسوق وفحص الأزواج..."):
    signals_list, prices_list = scan_market_signals()

# عرض أسعار السوق الحية للتأكد من الاتصال
if prices_list:
    st.subheader("📌 أسعار السوق الحية الحالية")
    st.dataframe(pd.DataFrame(prices_list), use_container_width=True)

st.markdown("---")
st.subheader("📊 سجل الإشارات والفرص المكتشفة")

if signals_list:
    st.success(f"تم رصد {len(signals_list)} إشارة خلال الفترة الأخيرة!")
    df_res = pd.DataFrame(signals_list)
    df_res = df_res.sort_values(by="الوقت", ascending=False)
    st.dataframe(df_res, use_container_width=True)
else:
    st.warning("⚪ لم يتم رصد إشارات تقاطع على هذا الفريم حالياً. جرب تغيير الإطار الزمني من القائمة الجانبية (مثلاً إلى 1h أو 30m) واضغط على زر التحديث في الأعلى.")
