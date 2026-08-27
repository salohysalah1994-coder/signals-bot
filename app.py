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
    page_title="ماسح الفرص + التنبيه الصوتي",
    page_icon="🔔",
    layout="wide"
)

st.title("🔔 روبوت الإشارات الفورية (مع التنبيه الصوتي والعداد)")
st.markdown("يقوم البوت بفحص كافة الأزواج تلقائياً وإصدار **صوت تنبيه (جرس)** فور توفر صفقة مؤكدة.")
st.markdown("---")

# ==========================================
# 2. دالة تشغيل التنبيه الصوتي
# ==========================================
def play_sound_alert():
    # ملف صوتي لجرس تنبيه يعمل عبر المتصفح
    audio_html = """
        <audio autoplay style="display:none;">
            <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# ==========================================
# 3. قائمة الأزواج والإعدادات
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

st.sidebar.header("⚙️ إعدادات التداول")
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني للفحص (الفريم):", ["5m", "1m", "15m"], index=0)
ENABLE_SOUND = st.sidebar.checkbox("🔊 تفعيل التنبيه الصوتي عند الصفقة", value=True)

duration_map = {"1m": 1, "5m": 5, "15m": 15}
trade_duration = duration_map.get(TIMEFRAME, 5)

# ==========================================
# 4. حساب العداد التنازلي
# ==========================================
def get_candle_countdown(timeframe_minutes):
    now = datetime.now()
    minutes_past = now.minute % timeframe_minutes
    seconds_past = now.second
    remaining_seconds = (timeframe_minutes * 60) - ((minutes_past * 60) + seconds_past)
    return remaining_seconds // 60, remaining_seconds % 60, remaining_seconds

# ==========================================
# 5. فحص البيانات والصفقات
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
            "signal": signal_type,
            "is_closed": is_market_closed
        }
    except Exception:
        return None

# ==========================================
# 6. العرض والتنبيهات
# ==========================================
mins_left, secs_left, total_rem_secs = get_candle_countdown(trade_duration)

st.subheader("⏳ العداد التنازلي لإغلاق الشمعة")
col_t1, col_t2 = st.columns([1, 2])
col_t1.metric("المتبقي للدخول", f"{mins_left:02d}:{secs_left:02d}")

if total_rem_secs <= 10:
    col_t2.error("🚨 **تنبيه:** باقي 10 ثوانٍ! جهّز دخول الصفقة فوراً عند وصول العداد لـ 00:00!")
else:
    col_t2.info("ℹ️ انتظر صفارة التنبيه أو وصول العداد لـ 00:00 لافتتاح الشمعة الجديدة.")

st.markdown("---")

with st.spinner("🔍 جاري فحص جميع الأزواج والبحث عن إشارات..."):
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
    st.error("🔴 **سوق الفوركس والذهب مغلق حالياً.**")
elif active_signals:
    # تشغيل الصفير/التنبيه الصوتي عند وجود صفقة
    if ENABLE_SOUND:
        play_sound_alert()
        
    st.success(f"🔔 **تم العثور على {len(active_signals)} صفقة حية ومؤكدة الآن!**")
    for item in active_signals:
        sig_text = "🟢 شراء (BUY)" if item['signal'] == 1 else "🔴 بيع (SELL)"
        st.write(f"### 📌 الزوج: **{item['name']}** | التوجيه: **{sig_text}** | مدة الصفقة: **{trade_duration} دقائق**")
        st.markdown("---")
else:
    st.warning("⚪ لا توجد إشارات حية حالياً. البوت يفحص باستمرار وسيصدر صفير فور ظهور صفقة جديدة.")

# تحديث تلقائي مستمر
if not market_is_off:
    time.sleep(2)
    st.rerun()
