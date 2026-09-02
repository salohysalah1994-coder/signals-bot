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
    page_title="ماسح صفقات الفوركس (24 ساعة) - صلاح",
    page_icon="📈",
    layout="wide"
)

st.title("📈 روبوت الفوركس (سجل صفقات آخر 24 ساعة) - صلاح")
st.markdown("البوت يقوم بمسح السوق وعرض كافة الإشارات والفرص التي ظهرت خلال الـ 24 ساعة الماضية.")
st.markdown("---")

# ==========================================
# 2. إدارة الذاكرة المؤقتة لسجل الصفقات
# ==========================================
if 'signal_history' not in st.session_state:
    st.session_state.signal_history = []

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
ENABLE_SOUND = st.sidebar.checkbox("🔊 تفعيل التنبيه الصوتي عند اكتشاف فرصة جديدة", value=True)
USE_EMA_FILTER = st.sidebar.checkbox("🛡️ تفعيل فلتر الاتجاه العام (EMA 200)", value=False)

# تحديد فترة جلب البيانات لتغطي آخر 24 ساعة وأكثر
period_map = {"5m": "2d", "15m": "5d", "30m": "5d", "1h": "7d"}
fetch_period = period_map.get(TIMEFRAME, "5d")

# ==========================================
# 5. دالة فحص وتاريخ الصفقات
# ==========================================
def scan_all_signals():
    all_found_signals = []
    
    for name, symbol in PAIRS_MAP.items():
        try:
            df = yf.download(symbol, period=fetch_period, interval=TIMEFRAME, progress=False)
            if df.empty or len(df) < 205:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df.reset_index()
            time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
            df['datetime'] = pd.to_datetime(df[time_col])
            close_series = df['Close'].squeeze()
            
            # المؤشرات الفنية
            sma_fast = ta.sma(close_series, length=5)
            sma_slow = ta.sma(close_series, length=34)
            buffer1 = sma_fast - sma_slow
            buffer2 = ta.wma(buffer1, length=5)
            rsi = ta.rsi(close_series, length=14)
            ema_200 = ta.ema(close_series, length=200)
            
            # فلترة الشموع التي وقعت خلال الـ 24 ساعة الماضية فقط
            last_24h_limit = datetime.now() - timedelta(hours=24)
            
            # فحص الشموع السابقة للبحث عن الإشارات
            for i in range(200, len(df) - 1):
                candle_dt = df['datetime'].iloc[i]
                
                # تخطي ما هو أقدم من 24 ساعة
                if candle_dt < last_24h_limit:
                    continue
                
                b1_now, b1_prev = buffer1.iloc[i], buffer1.iloc[i - 1]
                b2_now, b2_prev = buffer2.iloc[i], buffer2.iloc[i - 1]
                rsi_now = rsi.iloc[i]
                price_now = close_series.iloc[i]
                ema_val = ema_200.iloc[i] if ema_200 is not None else price_now
                
                raw_buy = (b1_now > b2_now) and (b1_prev <= b2_prev)
                raw_sell = (b1_now < b2_now) and (b1_prev >= b2_prev)
                
                signal_type = 0
                if raw_buy:
                    if rsi_now > 50:
                        if not use_ema or (use_ema and price_now > ema_val):
                            signal_type = 1
                elif raw_sell:
                    if rsi_now < 50:
                        if not use_ema or (use_ema and price_now < ema_val):
                            signal_type = -1
                
                if signal_type != 0:
                    all_found_signals.append({
                        "time": str(candle_dt),
                        "name": name,
                        "signal": "🟢 صعود (شراء)" if signal_type == 1 else "🔴 هبوط (بيع)",
                        "price": round(float(price_now), 4),
                        "rsi": round(float(rsi_now), 1)
                    })
        except Exception:
            continue
            
    return all_found_signals

# ==========================================
# 6. واجهة العرض والتحديث
# ==========================================
st.subheader("📊 سجل إشارات آخر 24 ساعة")

if st.button("🔄 تحديث ورصد السوق الآن"):
    with st.spinner("جاري فحص جميع الأزواج واستخراج صفقات الـ 24 ساعة الماضية..."):
        st.session_state.signal_history = scan_all_signals()

# التشغيل التلقائي للفحص عند فتح الصفحة لأول مرة
if 'executed_initial_scan' not in st.session_state:
    st.session_state.signal_history = scan_all_signals()
    st.session_state.executed_initial_scan = True

history = st.session_state.signal_history

if history:
    st.success(f"تم العثور على {len(history)} إشارة/صفقة خلال الـ 24 ساعة الماضية.")
    
    # تحويل البيانات إلى جدول مرتب لعرضها بوضوح
    df_signals = pd.DataFrame(history)
    df_signals = df_signals.sort_values(by="time", ascending=False) # الأحدث أولاً
    
    st.dataframe(df_signals, use_container_width=True)
else:
    st.warning("⚪ لم يتم رصد صفقات مطابقة للشروط خلال الـ 24 ساعة الماضية على هذا الفريم. جرب تغيير فريم الوقت أو إيقاف فلتر الاتجاه من القائمة الجانبية.")

st.markdown("---")
st.info("💡 نصيحة: يمكنك النقر فوق زر التحديث في أي وقت لإعادة فحص أحدث بيانات السوق وجلب الصفقات الجديدة.")
