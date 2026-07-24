import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time

# ضبط إعدادات الصفحة
st.set_page_config(page_title="TEAM7 Signal Dashboard", layout="wide")

st.title("📊 TEAM7 Trading Signals Dashboard")
st.caption("مؤشر إشارات التداول يدويًا لمنصة Pocket Option")

# ---------------------------------------------------------
# قائمة كاملة بأهم الأزواج الحقيقية (Yahoo Finance Tickers)
# ---------------------------------------------------------
PAIRS_DICT = {
    # الأزواج الرئيسية (Majors)
    "EUR/USD (اليورو / الدولار الأمريكي)": "EURUSD=X",
    "GBP/USD (الباوند / الدولار الأمريكي)": "GBPUSD=X",
    "USD/JPY (الدولار الأمريكي / الين الياباني)": "USDJPY=X",
    "AUD/USD (الدولار الأسترالي / الدولار الأمريكي)": "AUDUSD=X",
    "USD/CAD (الدولار الأمريكي / الدولار الكندي)": "USDCAD=X",
    "USD/CHF (الدولار الأمريكي / الفرنك السويسري)": "USDCHF=X",
    "NZD/USD (الدولار النيوزيلندي / الدولار الأمريكي)": "NZDUSD=X",
    
    # التقاطعات الكبرى (Crosses)
    "EUR/GBP (اليورو / الباوند)": "EURGBP=X",
    "EUR/JPY (اليورو / الين الياباني)": "EURJPY=X",
    "GBP/JPY (الباوند / الين الياباني)": "GBPJPY=X",
    "AUD/JPY (الدولار الأسترالي / الين الياباني)": "AUDJPY=X",
    "EUR/AUD (اليورو / الدولار الأسترالي)": "EURAUD=X",
    "EUR/CAD (اليورو / الدولار الكندي)": "EURCAD=X",
    "GBP/CAD (الباوند / الدولار الكندي)": "GBPCAD=X",
    "GBP/CHF (الباوند / الفرنك السويسري)": "GBPCHF=X",
    "AUD/CAD (الدولار الأسترالي / الدولار الكندي)": "AUDCAD=X",
    "AUD/NZD (الدولار الأسترالي / الدولار النيوزيلندي)": "AUDNZD=X",
    "CAD/JPY (الدولار الكندي / الين الياباني)": "CADJPY=X",
    "CHF/JPY (الفرنك السويسري / الين الياباني)": "CHFJPY=X",
    "NZD/JPY (الدولار النيوزيلندي / الين الياباني)": "NZDJPY=X",

    # السلع والمعادن (Commodities)
    "XAU/USD (الذهب / الدولار)": "GC=F",
    "XAG/USD (الفضة / الدولار)": "SI=F",
    "BTC/USD (البيتكوين / الدولار)": "BTC-USD"
}

# Sidebar - التحكم والإعدادات
st.sidebar.header("⚙️ إعدادات الزوج والتحديث")

# قائمة اختيار الزوج
selected_pair_name = st.sidebar.selectbox("اختر زوج العملات:", list(PAIRS_DICT.keys()))
symbol = PAIRS_DICT[selected_pair_name]

timeframe = st.sidebar.selectbox("الإطار الزمني (Timeframe):", ["1m", "2m", "5m", "15m"], index=2) # 5m يفضل لمنع التأخير
auto_refresh = st.sidebar.checkbox("تحديث تلقائي (كل 10 ثوانٍ)", value=True)

# دالة جلب البيانات وحساب المؤشر
def get_signals():
    df = yf.download(tickers=symbol, period="1d", interval=timeframe, progress=False)
    
    if df.empty or len(df) < 60:
        return None, "لا توجد بيانات كافية للزوج المختار حالياً."

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # حساب المتوسطات المتحركة الأسية (EMA 30 to 60)
    df['EMA30'] = ta.ema(df['Close'], length=30)
    df['EMA35'] = ta.ema(df['Close'], length=35)
    df['EMA40'] = ta.ema(df['Close'], length=40)
    df['EMA45'] = ta.ema(df['Close'], length=45)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    df['EMA60'] = ta.ema(df['Close'], length=60)

    # شروط الترتيب (Long & Short)
    df['colslowL'] = (df['EMA30'] > df['EMA35']) & (df['EMA35'] > df['EMA40']) & \
                     (df['EMA40'] > df['EMA45']) & (df['EMA45'] > df['EMA50']) & \
                     (df['EMA50'] > df['EMA60'])

    df['colslowS'] = (df['EMA30'] < df['EMA35']) & (df['EMA35'] < df['EMA40']) & \
                     (df['EMA40'] < df['EMA45']) & (df['EMA45'] < df['EMA50']) & \
                     (df['EMA50'] < df['EMA60'])

    # إشارات الشراء والبيع
    df['Buy_Signal'] = (~df['colslowL'].shift(1).fillna(False)) & df['colslowL']
    df['Sell_Signal'] = (~df['colslowS'].shift(1).fillna(False)) & df['colslowS']

    return df, None

# تنفيذ الجلب
df, error = get_signals()

if error:
    st.error(error)
else:
    latest = df.iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("الزوج الحالي", selected_pair_name.split(" ")[0])
    col2.metric("السعر الحالي", f"{latest['Close']:.5f}")
    
    status = "تذبذب / سوق عرضي"
    if latest['colslowL']:
        status = "🟢 اتجاه صاعد قوي"
    elif latest['colslowS']:
        status = "🔴 اتجاه هابط قوي"
    
    col3.metric("حالة الاتجاه", status)

    st.markdown("---")

    # تنبيه الإشارة للحظة الحالية
    if latest['Buy_Signal']:
        st.success(f"🚀 **إشارة شراء جديدة (BUY / CALL) على {selected_pair_name.split(' ')[0]}!**")
    elif latest['Sell_Signal']:
        st.error(f"🔻 **إشارة بيع جديدة (SELL / PUT) على {selected_pair_name.split(' ')[0]}!**")
    else:
        st.info("⏳ لا توجد إشارة دخول جديدة حالياً على هذا الزوج.")

    # جدول لآخر الشمعات
    st.subheader("📋 متابعة آخر الشمعات والإشارات")
    display_df = df[['Close', 'colslowL', 'colslowS', 'Buy_Signal', 'Sell_Signal']].tail(8)
    st.dataframe(display_df, use_container_width=True)

# التحديث التلقائي
if auto_refresh:
    time.sleep(10)
    st.rerun()
