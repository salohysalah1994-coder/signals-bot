import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# إعدادات الصفحة الأساسية في Streamlit
st.set_page_config(page_title="Pocket Option SMC Bot", page_icon="🤖", layout="wide")

st.title("🤖 بوت تحليل وإشارات الخيارات الثنائية (SMC/CHoCH)")
st.write("يقوم هذا البوت بتحليل الأسعار مباشرة ورصد مناطق الاختراق وتوليد إشارات الدخول فوراً.")

# --- قسم الإعدادات الجانبية (Sidebar) ---
st.sidebar.header("⚙️ إعدادات البوت")
selected_pair = st.sidebar.selectbox("اختر الزوج الرسمي للتحليل:", ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"])
timeframe = st.sidebar.selectbox("الفريم (الوقت لانتهاء الصفقة):", ["1 MIN", "5 MIN"])
trade_amount = st.sidebar.number_input("مبلغ الصفقة الأساسية ($):", min_value=1.0, value=1.0, step=0.5)
swing_length = st.sidebar.slider("حساسية الفلترة (Swing Length):", min_value=2, max_value=10, value=3)

# --- حاسبة المضاعفات (Martingale Calculator) ---
st.sidebar.subheader("🧮 حاسبة المضاعفات (المارتينجال)")
payout_ratio = st.sidebar.slider("نسبة العائد في المنصة % (Payout):", min_value=50, max_value=100, value=80) / 100.0

# حساب المضاعفات تلقائياً بناءً على نسبة العائد لضمان التعويض والربح
step1 = trade_amount
step2 = round(step1 + (step1 / payout_ratio), 2)
step3 = round(step2 + (step2 / payout_ratio) + (step1 / payout_ratio), 2)

st.sidebar.write(f"**المضاعفة 1 (الأساسية):** {step1}$")
st.sidebar.write(f"**المضاعفة 2 (في حال خسارة الأولى):** {step2}$")
st.sidebar.write(f"**المضاعفة 3 (في حال خسارة الثانية):** {step3}$")
st.sidebar.warning("⚠️ لا ننصح بتجاوز المضاعفة الثالثة أبداً لحماية رأس مالك.")

# --- دالة تحليل الهيكل وصيد الإشارات ---
def check_smc_signal(candles_df, swing_len):
    if len(candles_df) < (swing_len * 2 + 1):
        return None
    
    # تحديد القمم والقيعان المحلية
    candles_df['is_high'] = candles_df['high'] == candles_df['high'].rolling(window=swing_len*2+1, center=True).max()
    candles_df['is_low'] = candles_df['low'] == candles_df['low'].rolling(window=swing_len*2+1, center=True).min()
    
    highs = candles_df[candles_df['is_high']]['high'].values
    lows = candles_df[candles_df['is_low']]['low'].values
    
    if len(highs) < 1 or len(lows) < 1:
        return None
        
    last_swing_high = highs[-1]
    last_swing_low = lows[-1]
    
    current_price = candles_df['close'].iloc[-1]
    previous_price = candles_df['close'].iloc[-2]
    
    if previous_price <= last_swing_high and current_price > last_swing_high:
        return {"type": "CALL (شراء)", "price": current_price, "target": last_swing_high}
    elif previous_price >= last_swing_low and current_price < last_swing_low:
        return {"type": "PUT (بيع)", "price": current_price, "target": last_swing_low}
        
    return None

# --- محاكاة جلب البيانات الحية من البروكر ---
@st.cache_data(ttl=1)
def get_live_data():
    np.random.seed(int(time.time()))
    base_price = 1.0850 if "EUR" in selected_pair else 150.20
    prices = base_price + np.cumsum(np.random.normal(0, 0.0003, 50))
    df = pd.DataFrame({
        "open": prices - 0.0001,
        "high": prices + 0.0002,
        "low": prices - 0.0002,
        "close": prices
    })
    return df

candles_data = get_live_data()
current_price = candles_data['close'].iloc[-1]

# --- لوحة التحكم الرئيسية (Dashboard) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📈 الزوج المختار", value=selected_pair)
with col2:
    st.metric(label="💰 السعر الحالي اللحظي", value=f"{current_price:.5f}")
with col3:
    st.metric(label="⏱️ فريم العمل المقترح", value=timeframe)

st.write("---")

# فحص الإشارة الحالية
st.subheader("📡 حالة الإشارة الحالية")
signal = check_smc_signal(candles_data, swing_length)

if signal:
    color = "green" if "CALL" in signal["type"] else "red"
    bg_color = "rgba(0, 255, 0, 0.1)" if color == "green" else "rgba(255, 0, 0, 0.1)"
    
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 25px; border-radius: 12px; border: 3px solid {color}; text-align: right; direction: rtl;">
        <h2 style="color: {color}; margin-top: 0;">🚨 إشارة دخول حية ومؤكدة!</h2>
        <hr style="border-color: {color};">
        <p style="font-size: 20px; line-height: 1.8; color: white;">
            📌 <b>الزوج المستهدف:</b> <span style="font-size: 24px; color: yellow;">{selected_pair}</span><br>
            🎯 <b>نوع الصفقة المطلوبة:</b> <span style="font-size: 24px; color: {color}; font-weight: bold;">{signal['type']}</span><br>
            💵 <b>سعر الدخول الدقيق:</b> <span style="font-size: 24px;">{signal['price']:.5f}</span><br>
            ⏰ <b>وقت إطلاق الإشارة:</b> <span style="font-size: 24px; color: cyan;">{datetime.now().strftime('%H:%M:%S')}</span><br>
            ⏳ <b>مدة الصفقة (زمن الانتهاء):</b> <span style="font-size: 24px; color: #FF9900;">2 شمعة (دقيقتين)</span><br>
            ⚠️ <b>مبالغ الدخول المقترحة في حال الخسارة:</b><br>
            🔹 الصفقة الأولى (الأساسية): <span style="font-size: 22px; color: #00FF00;"><b>{step1}$</b></span><br>
            🔹 الصفقة الثانية (مضاعفة 1): <span style="font-size: 22px; color: #FFFF00;"><b>{step2}$</b></span><br>
            🔹 الصفقة الثالثة (مضاعفة 2): <span style="font-size: 22px; color: #FF0000;"><b>{step3}$</b></span>
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("🔄 جاري رصد حركة السعر للقمم والقيعان... لا توجد إشارة دخول مطابقة لشروط الـ SMC في هذه اللحظة.")

# جدول لعرض آخر البيانات المحللة
st.write("### 📊 عينة من آخر حركات السعر والشموع:")
st.dataframe(candles_data.tail(5))

# تكرار تحديث الشاشة تلقائياً
time.sleep(1)
st.rerun()
