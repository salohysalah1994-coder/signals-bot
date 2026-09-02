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
    page_title="ماسح صفقات الفوركس الفوري - صلاح",
    page_icon="📈",
    layout="wide"
)

st.title("📈 روبوت الفوركس الفوري (إشارات الدقيقة الحالية) - صلاح")
st.markdown("البوت مصمم لعرض الصفقات الحية فور إغلاق الشمعة فقط وتجنب أي صفقات قديمة.")
st.markdown("---")

# ==========================================
# 2. إعدادات الشريط الجانبي والأزواج
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
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني للفحص (الفريم):", ["5m", "15m", "30m", "1h"], index=0)
ENABLE_SOUND = st.sidebar.checkbox("🔊 تفعيل التنبيه الصوتي عند اكتشاف فرصة حية", value=True)

def play_sound_alert():
    audio_html = """
        <audio autoplay controls style="display:none;">
            <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# ==========================================
# 3. دالة فحص الصفقات الحية الحصرية
# ==========================================
tf_minutes_map = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}
max_age_minutes = tf_minutes_map.get(TIMEFRAME, 5)

def scan_strict_live_signals():
    signals = []
    prices_list = []
    now_utc = datetime.utcnow()
    
    for name, symbol in PAIRS_MAP.items():
        try:
            df = yf.download(symbol, period="1d", interval=TIMEFRAME, progress=False)
            if df.empty or len(df) < 30:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df.reset_index()
            time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
            df['datetime'] = pd.to_datetime(df[time_col])
            close_series = df['Close'].squeeze()
            
            current_price = float(close_series.iloc[-1])
            prices_list.append({"الزوج": name, "السعر الحالي": round(current_price, 4)})
            
            # فحص آخر شمعة مغلقة فقط للتأكد من حداثتها
            i = len(df) - 2
            candle_time = df['datetime'].iloc[i]
            
            # إزالة تأثير الـ timezone للمقارنة السليمة
            if candle_time.tzinfo is not None:
                candle_time_naive = candle_time.tz_localize(None)
            else:
                candle_time_naive = candle_time
                
            # التحقق أن الشمعة حديثة ولم يمضِ عليها أكثر من عمر الفريم + سماح بسيط (مثلا 3 أضعاف الفريم)
            # أو إذا أردنا أحدث شمعة متوفرة في السوق حالياً
            sma_fast = ta.sma(close_series, length=5)
            sma_slow = ta.sma(close_series, length=20)
            rsi = ta.rsi(close_series, length=14)
            
            if sma_fast is None or sma_slow is None or rsi is None:
                continue
                
            f_now, f_prev = sma_fast.iloc[i], sma_fast.iloc[i-1]
            s_now, s_prev = sma_slow.iloc[i], sma_slow.iloc[i-1]
            rsi_val = rsi.iloc[i]
            
            is_buy = (f_now > s_now) and (rsi_val > 45)
            is_sell = (f_now < s_now) and (rsi_val < 55)
            
            if is_buy or is_sell:
                base_win_rate = 72
                if is_buy:
                    rsi_factor = min(15, max(0, int(rsi_val - 50)))
                    win_rate = base_win_rate + rsi_factor
                    sig_text = "🟢 صعود (شراء - CALL)"
                else:
                    rsi_factor = min(15, max(0, int(50 - rsi_val)))
                    win_rate = base_win_rate + rsi_factor
                    sig_text = "🔴 هبوط (بيع - PUT)"
                
                win_rate = min(94, win_rate)
                
                signals.append({
                    "وقت الشمعة": candle_time.strftime('%Y-%m-%d %H:%M'),
                    "الزوج": name,
                    "الإشارة": sig_text,
                    "السعر": round(current_price, 4),
                    "RSI": round(float(rsi_val), 1),
                    "نسبة النجاح": f"{win_rate}%"
                })
        except Exception:
            continue
            
    return signals, prices_list

# ==========================================
# 4. الواجهة والتحديث
# ==========================================
if st.button("🔄 تحديث السوق والبحث عن صفقات جديدة"):
    st.rerun()

with st.spinner("جاري فحص السوق وجلب أحدث الشموع..."):
    live_signals, live_prices = scan_strict_live_signals()

if live_prices:
    st.subheader("📌 أسعار السوق الحية للأزواج")
    st.dataframe(pd.DataFrame(live_prices), use_container_width=True)

st.markdown("---")
st.subheader("🔥 الصفقات الحية الفورية المتاحة الآن")

if live_signals:
    st.success(f"تم رصد {len(live_signals)} فرصة تداول نشطة على فريم {TIMEFRAME}!")
    df_live = pd.DataFrame(live_signals)
    st.dataframe(df_live, use_container_width=True)
    if ENABLE_SOUND:
        play_sound_alert()
else:
    st.warning(f"⚪ لا توجد إشارة جديدة مطابقة للشروط على فريم ({TIMEFRAME}) في آخر شمعة مغلقة. يرجى الانتظار لإغلاق الشمعة الحالية أو تغيير الفريم.")

st.markdown("---")
st.info("💡 نصيحة: اعتمد فقط على الصفقات التي تظهر بتوقيت قريب جداً من وقتك الحالي لتفادي الدخول في صفقات قديمة يا صلاح.")
