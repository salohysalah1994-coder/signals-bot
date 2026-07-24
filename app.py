import streamlit as st
import pandas as pd
import time
from tvDatafeed import TvDatafeed, Interval

# ضبط إعدادات الصفحة
st.set_page_config(page_title="TEAM7 Signal Bot", layout="wide")

st.title("⚡ TEAM7 Direct Live Signals")
st.caption("إشارات تداول لحظية مباشرة بدون الذهاب إلى TradingView")

# الاتصال بسيرفر TradingView المباشر (حساب مجاني)
@st.cache_resource
def init_tv():
    return TvDatafeed()

tv = init_tv()

# قائمة أهم الأزواج من سيرفرات البورصة المباشرة (FXCM / OANDA)
PAIRS_DICT = {
    # الأزواج الرئيسية
    "EUR/USD": ("EURUSD", "FXCM"),
    "GBP/USD": ("GBPUSD", "FXCM"),
    "USD/JPY": ("USDJPY", "FXCM"),
    "AUD/USD": ("AUDUSD", "FXCM"),
    "USD/CAD": ("USDCAD", "FXCM"),
    "USD/CHF": ("USDCHF", "FXCM"),
    "NZD/USD": ("NZDUSD", "FXCM"),
    
    # التقاطعات والشارتات السريعة
    "EUR/GBP": ("EURGBP", "FXCM"),
    "EUR/JPY": ("EURJPY", "FXCM"),
    "GBP/JPY": ("GBPJPY", "FXCM"),
    "AUD/JPY": ("AUDJPY", "FXCM"),
    
    # السلع والعملات الرقمية (تشتغل 24/7)
    "الذهب (XAU/USD)": ("XAUUSD", "OANDA"),
    "البيتكوين (BTC/USD)": ("BTCUSD", "BITSTAMP"),
    "الإيثريوم (ETH/USD)": ("ETHUSD", "BITSTAMP")
}

# القائمة الجانبية
st.sidebar.header("⚙️ خيارات التداول")
selected_pair = st.sidebar.selectbox("اختر زوج العملات:", list(PAIRS_DICT.keys()))
symbol, exchange = PAIRS_DICT[selected_pair]

tf_option = st.sidebar.selectbox("الإطار الزمني:", ["1 minute", "5 minutes", "15 minutes"], index=0)

INTERVAL_MAP = {
    "1 minute": Interval.in_1_minute,
    "5 minutes": Interval.in_5_minute,
    "15 minutes": Interval.in_15_minute
}

auto_refresh = st.sidebar.checkbox("تحديث لحظي كـ Bot (كل 5 ثوانٍ)", value=True)

# دالة حساب EMA
def calculate_ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

# جلب البيانات اللحظية
def fetch_and_analyze():
    try:
        # جلب آخر 100 شمعة من TradingView مباشرة
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=INTERVAL_MAP[tf_option], n_bars=100)
        
        if df is None or df.empty:
            return None, "تعذر جلب البيانات اللحظية حالياً."

        # حساب المتوسطات الأسية لـ TEAM7
        df['EMA30'] = calculate_ema(df['close'], 30)
        df['EMA35'] = calculate_ema(df['close'], 35)
        df['EMA40'] = calculate_ema(df['close'], 40)
        df['EMA45'] = calculate_ema(df['close'], 45)
        df['EMA50'] = calculate_ema(df['close'], 50)
        df['EMA60'] = calculate_ema(df['close'], 60)

        # شروط الاتجاه
        df['colslowL'] = (df['EMA30'] > df['EMA35']) & (df['EMA35'] > df['EMA40']) & \
                         (df['EMA40'] > df['EMA45']) & (df['EMA45'] > df['EMA50']) & \
                         (df['EMA50'] > df['EMA60'])

        df['colslowS'] = (df['EMA30'] < df['EMA35']) & (df['EMA35'] < df['EMA40']) & \
                         (df['EMA40'] < df['EMA45']) & (df['EMA45'] < df['EMA50']) & \
                         (df['EMA50'] < df['EMA60'])

        # الإشارات
        df['Buy_Signal'] = (~df['colslowL'].shift(1).fillna(False)) & df['colslowL']
        df['Sell_Signal'] = (~df['colslowS'].shift(1).fillna(False)) & df['colslowS']

        return df, None
    except Exception as e:
        return None, f"خطأ أثناء جلب البيانات: {str(e)}"

df, error = fetch_and_analyze()

if error:
    st.error(error)
else:
    latest = df.iloc[-1]
    
    # عرض البيانات الرئيسية
    col1, col2, col3 = st.columns(3)
    col1.metric("الزوج", selected_pair)
    col2.metric("السعر اللحظي المباشر", f"{latest['close']:.5f}")
    
    status = "⚪ تذبذب / انتظار"
    if latest['colslowL']:
        status = "🟢 اتجاه صاعد قوي (BUY Zone)"
    elif latest['colslowS']:
        status = "🔴 اتجاه هابط قوي (SELL Zone)"
    
    col3.metric("حالة المؤشر", status)

    st.markdown("---")

    # تنبيه إشارة الشراء والبيع المباشر
    if latest['Buy_Signal']:
        st.success(f"🚨 **إشارة شراء الآن (CALL / BUY) على {selected_pair}!** - ادخل الصفقة في Pocket Option فوراً.")
    elif latest['Sell_Signal']:
        st.error(f"🚨 **إشارة بيع الآن (PUT / SELL) على {selected_pair}!** - ادخل الصفقة في Pocket Option فوراً.")
    else:
        st.info("⏳ لا توجد إشارة دخول جديدة على الشمعة الحالية. البوت يراقب السوق...")

    # جدول المتابعة اللحظية
    st.subheader("📋 متابعة آخر الشمعات")
    display_df = df[['close', 'colslowL', 'colslowS', 'Buy_Signal', 'Sell_Signal']].tail(6)
    st.dataframe(display_df, use_container_width=True)

# إعادة التحديث التلقائي كل 5 ثوانٍ
if auto_refresh:
    time.sleep(5)
    st.rerun()
