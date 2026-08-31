import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import time
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="ماسح صفقات الفوركس الحقيقي - صلاح",
    page_icon="📈",
    layout="wide"
)

st.title("📈 روبوت الفوركس الحقيقي (تحديث فوري وحصري) - صلاح")
st.markdown("البوت مبرمج لإظهار الإشارات في أول دقيقة من الشمعة ومسحها فور انتهاء وقت الدخول.")
st.markdown("---")

# ==========================================
# 2. إدارة الذاكرة المؤقتة
# ==========================================
if 'active_signal' not in st.session_state:
    st.session_state.active_signal = None
if 'signal_candle_time' not in st.session_state:
    st.session_state.signal_candle_time = None

# ==========================================
# 3. دالة تشغيل التنبيه الصوتي
# ==========================================
def play_sound_alert():
    audio_html = """
        <audio autoplay controls style="display:none;">
            <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# ==========================================
# 4. قائمة أزواج الفوركس الحقيقية والإعدادات
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
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني للفحص (الفريم):", ["15m", "30m", "1h", "5m"], index=0)
ENABLE_SOUND = st.sidebar.checkbox("🔊 تفعيل التنبيه الصوتي عند الصفقة", value=True)
USE_EMA_FILTER = st.sidebar.checkbox("🛡️ تفعيل فلتر الاتجاه العام (EMA 200)", value=True)

duration_map = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60}
trade_duration = duration_map.get(TIMEFRAME, 15)

# ==========================================
# 5. حساب العداد التنازلي وقت الشمعة
# ==========================================
def get_candle_countdown(timeframe_minutes):
    now = datetime.now()
    minutes_past = now.minute % timeframe_minutes
    seconds_past = now.second
    total_seconds_in_candle = timeframe_minutes * 60
    remaining_seconds = total_seconds_in_candle - ((minutes_past * 60) + seconds_past)
    elapsed_seconds = (minutes_past * 60) + seconds_past
    return remaining_seconds // 60, remaining_seconds % 60, remaining_seconds, elapsed_seconds

# ==========================================
# 6. فحص البيانات بالشمعة المغلقة
# ==========================================
def scan_forex_strategy(name, symbol, timeframe, use_ema):
    try:
        df = yf.download(symbol, period="5d", interval=timeframe, progress=False)
        if df.empty or len(df) < 205:
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
        ema_200 = ta.ema(close_series, length=200)
        
        last_idx = len(df) - 2 
        if last_idx < 200:
            return None
            
        candle_time = str(df['datetime'].iloc[last_idx])
        
        b1_now, b1_prev = buffer1.iloc[last_idx], buffer1.iloc[last_idx - 1]
        b2_now, b2_prev = buffer2.iloc[last_idx], buffer2.iloc[last_idx - 1]
        rsi_now = rsi.iloc[last_idx]
        price_now = close_series.iloc[last_idx]
        ema_val = ema_200.iloc[last_idx] if ema_200 is not None else price_now
        
        raw_buy = (b1_now > b2_now) and (b1_prev <= b2_prev)
        raw_sell = (b1_now < b2_now) and (b1_prev >= b2_prev)
        
        signal_type = 0
        if raw_buy:
            if rsi_now > 52:
                if not use_ema or (use_ema and price_now > ema_val):
                    signal_type = 1
        elif raw_sell:
            if rsi_now < 48:
                if not use_ema or (use_ema and price_now < ema_val):
                    signal_type = -1
            
        return {
            "name": name,
            "symbol": symbol,
            "price": price_now,
            "rsi": rsi_now,
            "signal": signal_type,
            "candle_time": candle_time
        }
    except Exception:
        return None

# ==========================================
# 7. العرض والتحكم الصارم بوقت الصلاحية
# ==========================================
mins_left, secs_left, total_rem_secs, elapsed_secs = get_candle_countdown(trade_duration)

st.subheader("⏳ العداد التنازلي لإغلاق الشمعة الحالية")
col_t1, col_t2 = st.columns([1, 2])
col_t1.metric("الوقت المتبقي لإغلاق الشمعة", f"{mins_left:02d}:{secs_left:02d}")
col_t2.info("📈 الإشارات تظهر حصرياً في أول دقيقتين من الشمعة وتختفي تلقائياً بعدها لمنع أي صفقات قديمة.")

st.markdown("---")

# شرط الحذف القاطع: إذا مرّت أول دقيقتين من الشمعة (أصبح الوقت المنقضي أكثر من 120 ثانية)، نقوم بمسح الصفقة تماماً
TOTAL_CANDLE_SECONDS = trade_duration * 60
if elapsed_secs > 120 or total_rem_secs < 120:
    st.session_state.active_signal = None
    st.session_state.signal_candle_time = None

# فحص السوق فقط إذا كنا في أول دقيقتين من الشمعة ولم يتم تسجيل صفقة لهذه الشمعة بعد
if elapsed_secs <= 120 and st.session_state.active_signal is None:
    with st.spinner("🔍 جاري البحث عن فرصة جديدة في افتتاح الشمعة..."):
        current_time_str = datetime.now().strftime("%H:%M:%S")
        for name, sym in PAIRS_MAP.items():
            res = scan_forex_strategy(name, sym, TIMEFRAME, USE_EMA_FILTER)
            if res is not None and res['signal'] != 0:
                # التأكد أن الشمعة المكتشفة هي الشمعة الحقيقية الحالية وليست قديمة
                res['time'] = current_time_str
                st.session_state.active_signal = res
                st.session_state.signal_candle_time = res['candle_time']
                if ENABLE_SOUND:
                    play_sound_alert()
                break

# عرض الصفقة فقط إذا كانت موجودة وضمن نافذة الوقت الصحيحة
if st.session_state.active_signal is not None and elapsed_secs <= 120:
    item = st.session_state.active_signal
    st.success("🔥 **فرصة فوركس حقيقية جديدة ومتاحة للدخول الآن!**")
    sig_text = "🟢 صعود (CALL) - شراء" if item['signal'] == 1 else "🔴 هبوط (PUT) - بيع"
    st.write(f"⏱️ **وقت التوليد:** `{item['time']}` | 📌 الزوج: **{item['name']}**")
    st.write(f"التوجيه: **{sig_text}** | السعر: **{item['price']:.4f}** | RSI: **{item['rsi']:.1f}**")
    st.markdown("---")
else:
    st.warning("⚪ البوت يعمل بانتظار الشمعة القادمة... سيتم إخفاء أي صفقة فور انتهاء دقيقتها الأولى لضمان الأمان يا صلاح.")

# تحديث تلقائي مستمر
time.sleep(3)
st.rerun()
