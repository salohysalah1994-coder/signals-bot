import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import time
from datetime import datetime, timedelta

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="ماسح الفرص والإشارات الفورية الذكي",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 ماسح الأسواق التلقائي (مع التحقق من فتح السوق)")
st.markdown("يقوم البوت بفحص الأزواج والذهب تلقائياً ويستبعد أي بيانات قديمة إذا كان السوق مغلقاً.")
st.markdown("---")

# ==========================================
# 2. قائمة الأزواج المراد فحصها
# ==========================================
PAIRS_MAP = {
    "الذهب (XAU/USD)": "GC=F",
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
    "EUR/AUD": "EURAUD=X",
    "EUR/CAD": "EURCAD=X",
    "GBP/CAD": "GBPCAD=X",
    "AUD/JPY": "AUDJPY=X"
}

# ==========================================
# 3. القائمة الجانبية
# ==========================================
st.sidebar.header("⚙️ إعدادات الفحص والتكرار")
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني للفحص (الفريم):", ["5m", "1m", "15m"], index=0)
AUTO_SCAN = st.sidebar.checkbox("🔄 تفعيل الفحص التلقائي المستمر", value=True)

duration_map = {"1m": 1, "5m": 5, "15m": 15}
trade_duration = duration_map.get(TIMEFRAME, 5)

# ==========================================
# 4. دالة فحص الزوج مع التأكد من حداثة البيانات
# ==========================================
def scan_single_pair(name, symbol, timeframe):
    try:
        df = yf.download(symbol, period="1d", interval=timeframe, progress=False)
        if df.empty:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.reset_index()
        time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
        df['datetime'] = pd.to_datetime(df[time_col])
        
        close_series = df['Close'].squeeze()
        
        # مؤشرات الفلترة
        sma_fast = ta.sma(close_series, length=5)
        sma_slow = ta.sma(close_series, length=34)
        buffer1 = sma_fast - sma_slow
        buffer2 = ta.wma(buffer1, length=5)
        rsi = ta.rsi(close_series, length=14)
        
        last_idx = len(df) - 1
        if last_idx < 2:
            return None
            
        time_now = df['datetime'].iloc[last_idx]
        
        # التحقق هل الشمعة حديثة أم قديمة (إذا كانت أقدم من 20 دقيقة يعتبر السوق مغلقاً)
        # نحول التوقيت للتوقيت المحلي للتحقق
        is_market_closed = False
        time_diff = (datetime.utcnow() - time_now.tz_localize(None)).total_seconds() / 60
        if time_diff > 30: # إذا كان الفارق أكثر من 30 دقيقة
            is_market_closed = True
            
        b1_now, b1_prev = buffer1.iloc[last_idx], buffer1.iloc[last_idx - 1]
        b2_now, b2_prev = buffer2.iloc[last_idx], buffer2.iloc[last_idx - 1]
        rsi_now = rsi.iloc[last_idx]
        price_now = close_series.iloc[last_idx]
        
        raw_buy = (b1_now > b2_now) and (b1_prev <= b2_prev)
        raw_sell = (b1_now < b2_now) and (b1_prev >= b2_prev)
        
        signal_type = 0
        if not is_market_closed:
            if raw_buy and rsi_now > 50:
                signal_type = 1
            elif raw_sell and rsi_now < 50:
                signal_type = -1
            
        return {
            "name": name,
            "symbol": symbol,
            "price": price_now,
            "rsi": rsi_now,
            "time": time_now,
            "signal": signal_type,
            "is_closed": is_market_closed
        }
    except Exception:
        return None

# ==========================================
# 5. تشغيل الفحص على كافة الأزواج
# ==========================================
with st.spinner("🔍 جاري فحص حالة السوق والأزواج..."):
    active_signals = []
    all_market_status = []
    market_is_off = False
    
    for name, sym in PAIRS_MAP.items():
        res = scan_single_pair(name, sym, TIMEFRAME)
        if res is not None:
            all_market_status.append(res)
            if res['is_closed']:
                market_is_off = True
            elif res['signal'] != 0:
                active_signals.append(res)

# ==========================================
# 6. عرض النتائج
# ==========================================
if market_is_off:
    st.error("🔴 **سوق الفوركس والذهب مغلق حالياً (العطلة الأسبوعية).**\n\nتتوقف الأسعار والإشارات تلقائياً حتى افتتاح السوق الرسمي مساء الأحد.")

elif active_signals:
    st.success(f"🔥 تم العثور على {len(active_signals)} فرصة تداول مفلترة حية الآن!")
    
    for item in active_signals:
        next_entry_time = item['time'] + timedelta(minutes=trade_duration)
        entry_time_str = next_entry_time.strftime('%H:%M:%S')
        
        with st.container():
            col1, col2, col3 = st.columns(3)
            col1.subheader(f"📌 {item['name']}")
            col2.metric("السعر الحالي", f"{item['price']:.5f}" if "JPY" not in item['symbol'] and "GC" not in item['symbol'] else f"{item['price']:.2f}")
            col3.metric("RSI", f"{item['rsi']:.1f}")
            
            if item['signal'] == 1:
                st.success(
                    f"🟢 **إشارة شراء (BUY)**\n\n"
                    f"* 🎯 **وقت الدخول:** ادخل عند الدقيقة `{entry_time_str}` بالضبط.\n"
                    f"* ⏱️ **مدة الصفقة:** `{trade_duration} دقائق`."
                )
            else:
                st.error(
                    f"🔴 **إشارة بيع (SELL)**\n\n"
                    f"* 🎯 **وقت الدخول:** ادخل عند الدقيقة `{entry_time_str}` بالضبط.\n"
                    f"* ⏱️ **مدة الصفقة:** `{trade_duration} دقائق`."
                )
            st.markdown("---")
else:
    st.warning("⚪ لا توجد إشارات جديدة حية حالياً. البوت يستمر بالفحص المباشر...")

# جدول حالة السوق الكلية
st.subheader("📊 حالة جميع الأزواج المفحوصة")
if all_market_status:
    df_status = pd.DataFrame(all_market_status)
    df_status['الحالة'] = df_status.apply(
        lambda r: '🔴 السوق مغلق' if r['is_closed'] else ('🟢 شراء جاهز' if r['signal'] == 1 else ('🔴 بيع جاهز' if r['signal'] == -1 else '⚪ انتظار')), 
        axis=1
    )
    df_status['السعر'] = df_status.apply(lambda r: f"{r['price']:.5f}" if "JPY" not in r['symbol'] and "GC" not in r['symbol'] else f"{r['price']:.2f}", axis=1)
    df_status['RSI'] = df_status['rsi'].round(1)
    
    st.dataframe(df_status[['name', 'السعر', 'RSI', 'الحالة']], use_container_width=True)

# ==========================================
# 7. التحديث التلقائي
# ==========================================
if AUTO_SCAN and not market_is_off:
    time.sleep(60)
    st.rerun()
