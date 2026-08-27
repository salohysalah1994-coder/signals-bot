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
    page_title="ماسح الفرص + العداد التنازلي",
    page_icon="⏱️",
    layout="wide"
)

st.title("⏱️ ماسح الفرص مع العداد التنازلي المباشر")
st.markdown("يقوم البوت بفحص الأسواق ويعرض العداد التنازلي المتبقي لإغلاق الشمعة الحالية لضمان الدخول في اللحظة الدقيقة.")
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
    "GBP/JPY": "GBPJPY=X"
}

# ==========================================
# 3. القائمة الجانبية
# ==========================================
st.sidebar.header("⚙️ إعدادات الفحص والتوقيت")
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني للفحص (الفريم):", ["5m", "1m", "15m"], index=0)

duration_map = {"1m": 1, "5m": 5, "15m": 15}
trade_duration = duration_map.get(TIMEFRAME, 5)

# ==========================================
# 4. دالة حساب الوقت المتبقي للشمعة الحالية
# ==========================================
def get_candle_countdown(timeframe_minutes):
    now = datetime.now()
    minutes_past = now.minute % timeframe_minutes
    seconds_past = now.second
    
    total_seconds_passed = (minutes_past * 60) + seconds_past
    total_seconds_in_candle = timeframe_minutes * 60
    
    remaining_seconds = total_seconds_in_candle - total_seconds_passed
    
    mins_left = remaining_seconds // 60
    secs_left = remaining_seconds % 60
    
    return mins_left, secs_left, remaining_seconds

# ==========================================
# 5. دالة فحص الزوج
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
        
        time_diff = (datetime.utcnow() - time_now.tz_localize(None)).total_seconds() / 60
        is_market_closed = time_diff > 30
            
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
# 6. عرض العداد المباشر والفرص
# ==========================================
mins_left, secs_left, total_rem_secs = get_candle_countdown(trade_duration)

# عرض شريط العداد والتنبيه
st.subheader("⏳ حالة الشمعة الحالية")
col_time1, col_time2 = st.columns([1, 2])

col_time1.metric("الوقت المتبقي لإغلاق الشمعة", f"{mins_left:02d}:{secs_left:02d}")

if total_rem_secs <= 10:
    col_time2.error("🚨 **تنبيه عاجل:** الشمعة على وشك الإغلاق! جهّز نفسك للدخول فوراً مع بداية الشمعة الجديدة!")
elif total_rem_secs <= 30:
    col_time2.warning("⚠️ **استعداد:** باقي أقل من 30 ثانية. افتح المنصة وجهّز مبلغ الصفقة.")
else:
    col_time2.info("ℹ️ الشمعة جارية حالياً. انتظر انتهاء العداد التنازلي لإغلاقها.")

st.markdown("---")

# فحص الأزواج
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

if market_is_off:
    st.error("🔴 **سوق الفوركس والذهب مغلق حالياً (العطلة الأسبوعية).**")

elif active_signals:
    st.success(f"🔥 تم العثور على {len(active_signals)} فرصة تداول مفلترة حية الآن!")
    
    for item in active_signals:
        with st.container():
            col1, col2, col3 = st.columns(3)
            col1.subheader(f"📌 {item['name']}")
            col2.metric("السعر الحالي", f"{item['price']:.5f}" if "JPY" not in item['symbol'] and "GC" not in item['symbol'] else f"{item['price']:.2f}")
            col3.metric("RSI", f"{item['rsi']:.1f}")
            
            sig_text = "🟢 شراء (BUY)" if item['signal'] == 1 else "🔴 بيع (SELL)"
            
            st.markdown(
                f"🎯 **توجيه الصفقة:**\n"
                f"* **النوع:** {sig_text}\n"
                f"* **توقيت التنفيذ:** ادخل فور انتهاء العداد اعلاه عند الوصول لـ `00:00`.\n"
                f"* **مدة الصفقة:** `{trade_duration} دقائق`."
            )
            st.markdown("---")
else:
    st.warning("⚪ لا توجد إشارات جديدة حية حالياً. البوت يستمر بالفحص المباشر...")

# جدول حالة جميع الأزواج
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

# تحديث الصفحة كل ثانية عند اقتراب الإغلاق
if not market_is_off:
    time.sleep(2)
    st.rerun()
