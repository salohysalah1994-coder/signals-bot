import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta

# ==========================================
# 1. إعدادات الصفحة في Streamlit
# ==========================================
st.set_page_config(
    page_title="GO Strategy Trading Signals",
    page_icon="📈",
    layout="wide"
)

st.title("📈 بوت إشارات التداول المطور (GO Strategy)")
st.caption("مخصص لصفقات الخيارات الثنائية والأسواق المالية (2 إلى 15 دقيقة)")

# ==========================================
# 2. القائمة الجانبية للإعدادات (Sidebar)
# ==========================================
st.sidebar.header("⚙️ إعدادات البوت")

SYMBOL = st.sidebar.text_input("رمز الزوج (Symbol)", value="EURUSD=X")
TIMEFRAME = st.sidebar.selectbox("الفريم الزمني", ["1m", "2m", "5m", "15m"], index=2)

st.sidebar.subheader("مؤشرات الاستراتيجية")
AO_FAST = st.sidebar.number_input("AO Fast Period", value=1)
AO_SLOW = st.sidebar.number_input("AO Slow Period", value=34)
SIGNAL_WMA = st.sidebar.number_input("Signal WMA Period", value=5)
TREND_EMA = st.sidebar.number_input("Trend Filter (EMA)", value=200)
RSI_PERIOD = st.sidebar.number_input("RSI Period", value=14)

# ==========================================
# 3. دالة جلب البيانات وتحليلها
# ==========================================
def fetch_and_analyze_data(symbol, timeframe):
    # جلب البيانات عبر yfinance
    df = yf.download(tickers=symbol, period="5d", interval=timeframe, progress=False)
    
    if df.empty:
        return None

    # معالجة أعمدة Pandas MultiIndex إن وجدت
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 1. حساب مؤشر GO Strategy (Awesome Oscillator)
    df['sma_fast'] = ta.sma(df['Close'], length=AO_FAST)
    df['sma_slow'] = ta.sma(df['Close'], length=AO_SLOW)
    df['buffer1'] = df['sma_fast'] - df['sma_slow']
    df['buffer2'] = ta.wma(df['buffer1'], length=SIGNAL_WMA)

    # 2. إضافة الفلاتر (EMA 200 & RSI 14)
    df['ema_200'] = ta.ema(df['Close'], length=TREND_EMA)
    df['rsi'] = ta.rsi(df['Close'], length=RSI_PERIOD)

    # 3. حساب شروط التقاطع الصارمة
    cross_up = (df['buffer1'] > df['buffer2']) & (df['buffer1'].shift(1) <= df['buffer2'].shift(1))
    cross_down = (df['buffer1'] < df['buffer2']) & (df['buffer1'].shift(1) >= df['buffer2'].shift(1))

    # شروط الشراء والبيع
    df['CALL'] = cross_up & (df['Close'] > df['ema_200']) & (df['rsi'] < 70)
    df['PUT'] = cross_down & (df['Close'] < df['ema_200']) & (df['rsi'] > 30)

    return df

# زر لتحديث البيانات يدوياً
if st.button("🔄 تحديث الإشارات الآن"):
    st.rerun()

# ==========================================
# 4. عرض النتائج والتنبيهات
# ==========================================
data = fetch_and_analyze_data(SYMBOL, TIMEFRAME)

if data is None or data.empty:
    st.error("❌ تعذر جلب البيانات. تأكد من صحة رمز الزوج (مثال: EURUSD=X أو GBPUSD=X).")
else:
    # الحصول على آخر شمعتين
    last_candle = data.iloc[-1]
    previous_candle = data.iloc[-2]

    current_price = round(float(last_candle['Close']), 5)
    last_time = last_candle.name

    # عرض كروت البيانات السريعة
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("السعر الحالي", f"{current_price}")
    col2.metric("RSI (14)", f"{round(float(last_candle['rsi']), 2) if not pd.isna(last_candle['rsi']) else 'N/A'}")
    col3.metric("الفريم", TIMEFRAME)
    col4.metric("آخر تحديث", f"{last_time.strftime('%H:%M:%S UTC')}")

    st.markdown("---")

    # فحص الإشارات على الشمعة المغلقة حديثاً
    if previous_candle['CALL']:
        st.success(f"🚀 **إشارة شراء قوية (CALL)** | الوقت: {previous_candle.name.strftime('%H:%M')} | السعر: {round(float(previous_candle['Close']), 5)}")
        st.info("💡 **التوصية:** ادخل صفقة **صعود (CALL)** مدتها 2 إلى 3 شمعات على منصة Pocket Option.")
    elif previous_candle['PUT']:
        st.error(f"🔻 **إشارة بيع قوية (PUT)** | الوقت: {previous_candle.name.strftime('%H:%M')} | السعر: {round(float(previous_candle['Close']), 5)}")
        st.info("💡 **التوصية:** ادخل صفقة **هبوط (PUT)** مدتها 2 إلى 3 شمعات على منصة Pocket Option.")
    else:
        st.warning("⏳ **لا توجد إشارات دخول حاسمة في الوقت الحالي.** انتظر الشمعة القادمة...")

    # عرض جدول بآخر الشموع والتفاصيل
    st.subheader("📋 سجل الشموع الأخيرة والمؤشرات")
    display_df = data[['Close', 'rsi', 'buffer1', 'buffer2', 'CALL', 'PUT']].tail(10)
    st.dataframe(display_df, use_container_width=True)
