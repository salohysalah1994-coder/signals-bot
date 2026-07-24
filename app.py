import streamlit as st
import yfinance as yf
import pandas as pd
import time

# ضبط إعدادات الصفحة
st.set_page_config(page_title="TEAM7 Signal Dashboard", page_icon="⚡", layout="wide")

st.title("⚡ TEAM7 Trading Signals Dashboard")
st.caption("مؤشر إشارات التداول يدويًا لمنصة Pocket Option (إطار 5 دقائق)")

# القائمة الشاملة لأزواج العملات والسلع
PAIRS_DICT = {
    # 1. الأزواج الرئيسية (Forex Majors)
    "EUR/USD (اليورو / الدولار)": "EURUSD=X",
    "GBP/USD (الباوند / الدولار)": "GBPUSD=X",
    "USD/JPY (الدولار / الين)": "USDJPY=X",
    "AUD/USD (الأسترالي / الدولار)": "AUDUSD=X",
    "USD/CAD (الدولار / الكندي)": "USDCAD=X",
    "USD/CHF (الدولار / الفرنك)": "USDCHF=X",
    "NZD/USD (النيوزيلندي / الدولار)": "NZDUSD=X",

    # 2. تقاطعات اليورو والباوند (EUR & GBP Crosses)
    "EUR/GBP (اليورو / الباوند)": "EURGBP=X",
    "EUR/JPY (اليورو / الين)": "EURJPY=X",
    "GBP/JPY (الباوند / الين)": "GBPJPY=X",
    "EUR/AUD (اليورو / الأسترالي)": "EURAUD=X",
    "EUR/CAD (اليورو / الكندي)": "EURCAD=X",
    "GBP/CAD (الباوند / الكندي)": "GBPCAD=X",
    "GBP/CHF (الباوند / الفرنك)": "GBPCHF=X",

    # 3. المعادن والسلع والعملات الرقمية
    "XAU/USD (الذهب)": "GC=F",
    "XAG/USD (الفضة)": "SI=F",
    "BTC/USD (البيتكوين)": "BTC-USD",
    "ETH/USD (الإيثريوم)": "ETH-USD"
}

# Sidebar - القائمة الجانبية (افتح السهم >> لتغيير الزوج)
st.sidebar.header("⚙️ إعدادات التحكم")

selected_pair_name = st.sidebar.selectbox("اختر زوج العملات:", list(PAIRS_DICT.keys()))
symbol = PAIRS_DICT[selected_pair_name]

# الإطار الزمني افتراضياً على 5m
timeframe = st.sidebar.selectbox("الإطار الزمني (Timeframe):", ["5m", "1m", "15m"], index=0)
auto_refresh = st.sidebar.checkbox("تحديث تلقائي (كل 10 ثوانٍ)", value=True)

# دالة حساب EMA المباشرة عبر Pandas
def calculate_ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

# دالة جلب البيانات وحساب إشارات TEAM7
def get_signals():
    try:
        df = yf.download(tickers=symbol, period="5d", interval=timeframe, progress=False)
        
        if df.empty or len(df) < 60:
            return None, "تعذر جلب البيانات لهذا الزوج حالياً، اختر زوجاً آخر من القائمة الجانبية."

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # حساب المتوسطات الأسية الستة
        df['EMA30'] = calculate_ema(df['Close'], 30)
        df['EMA35'] = calculate_ema(df['Close'], 35)
        df['EMA40'] = calculate_ema(df['Close'], 40)
        df['EMA45'] = calculate_ema(df['Close'], 45)
        df['EMA50'] = calculate_ema(df['Close'], 50)
        df['EMA60'] = calculate_ema(df['Close'], 60)

        # شروط الترتيب والاتجاه
        df['colslowL'] = (df['EMA30'] > df['EMA35']) & (df['EMA35'] > df['EMA40']) & \
                         (df['EMA40'] > df['EMA45']) & (df['EMA45'] > df['EMA50']) & \
                         (df['EMA50'] > df['EMA60'])

        df['colslowS'] = (df['EMA30'] < df['EMA35']) & (df['EMA35'] < df['EMA40']) & \
                         (df['EMA40'] < df['EMA45']) & (df['EMA45'] < df['EMA50']) & \
                         (df['EMA50'] < df['EMA60'])

        # الإشارات
        df['Buy_Signal'] = df['colslowL']
        df['Sell_Signal'] = df['colslowS']

        return df, None
    except Exception as e:
        return None, f"حدث خطأ أثناء الاتصال بالبيانات: {str(e)}"

# زر التحديث المباشر
if st.button("🔄 فحص وتحديث الإشارة الآن", use_container_width=True, type="primary"):
    st.rerun()

st.markdown("---")

# تنفيذ الفحص
df, error = get_signals()

if error:
    st.error(error)
else:
    latest = df.iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("الزوج الحالي", selected_pair_name.split(" ")[0])
    col2.metric("السعر اللحظي", f"{latest['Close']:.5f}")
    
    status = "⚪ تذبذب / انتظار"
    if latest['colslowL']:
        status = "🟢 اتجاه صاعد قوي (BUY Zone)"
    elif latest['colslowS']:
        status = "🔴 اتجاه هابط قوي (SELL Zone)"
    
    col3.metric("حالة المؤشر (5M)", status)

    st.markdown("---")

    # تنبيه الصفقة المحددة بـ 5 دقائق
    if latest['Buy_Signal']:
        st.success(f"🚀 **منطقة شراء صريحة (CALL / BUY) على {selected_pair_name.split(' ')[0]}!**\n\n⏱️ **مدة الصفقة في Pocket Option:** 5 دقائق بالضبط.")
    elif latest['Sell_Signal']:
        st.error(f"🔻 **منطقة بيع صريحة (PUT / SELL) على {selected_pair_name.split(' ')[0]}!**\n\n⏱️ **مدة الصفقة في Pocket Option:** 5 دقائق بالضبط.")
    else:
        st.info("⏳ السوق في حالة تذبذب حالياً. افتح القائمة الجانبية (<<) واختر زوجاً آخر.")

    # جدول متابعة الشمعات الأخيرة
    st.subheader("📋 متابعة آخر شمعات (فريم 5 دقائق)")
    display_df = df[['Close', 'colslowL', 'colslowS', 'Buy_Signal', 'Sell_Signal']].tail(6)
    st.dataframe(display_df, use_container_width=True)

# التحديث التلقائي
if auto_refresh:
    time.sleep(10)
    st.rerun()
