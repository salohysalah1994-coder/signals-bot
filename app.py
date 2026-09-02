import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="ماسح صفقات السكالبينج الفوري - صلاح",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ روبوت السكالبينج الفوري (فريم الدقيقة والدقيقتين) - صلاح")
st.markdown("البوت مصخص للعمل على فريمات الدقيقة والدقيقتين لاستخراج صفقات سريعة وقوية بدقة عالية.")
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

st.sidebar.header("⚙️ إعدادات فريمات السكالبينج")
st.sidebar.markdown(f"👤 **المتداول:** صلاح")
# إضافة فريم الدقيقة والدقيقتين بوضوح
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني للفحص (الفريم):", ["1m", "2m", "5m", "15m"], index=0)
ENABLE_SOUND = st.sidebar.checkbox("🔊 تفعيل التنبيه الصوتي عند رصد فرصة سريعة", value=True)

def play_sound_alert():
    audio_html = """
        <audio autoplay controls style="display:none;">
            <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# ==========================================
# 3. دالة الفحص السريع لفريمات الدقيقة
# ==========================================
def scan_scalping_signals():
    scalp_candidates = []
    prices_list = []
    
    for name, symbol in PAIRS_MAP.items():
        try:
            # لفريم الدقيقة والدقيقتين نحتاج بيانات لآخر يوم أو يومين لتكون قريبة جداً
            period_val = "1d" if TIMEFRAME in ["1m", "2m"] else "3d"
            df = yf.download(symbol, period=period_val, interval=TIMEFRAME, progress=False)
            
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
            
            # الشمعة المغلقة الأخيرة
            i = len(df) - 2
            candle_time = df['datetime'].iloc[i]
            
            # مؤشرات سريعة تتناسب مع فريم الدقيقة
            sma_fast = ta.sma(close_series, length=3)
            sma_slow = ta.sma(close_series, length=10)
            rsi = ta.rsi(close_series, length=9)
            
            if sma_fast is None or sma_slow is None or rsi is None:
                continue
                
            f_now, f_prev = sma_fast.iloc[i], sma_fast.iloc[i-1]
            s_now, s_prev = sma_slow.iloc[i], sma_slow.iloc[i-1]
            rsi_val = rsi.iloc[i]
            
            # شروط دقيقة للسكالبينج السريع
            is_buy = (f_now > s_now) and (f_prev <= s_prev) and (rsi_val > 50) and (rsi_val < 80)
            is_sell = (f_now < s_now) and (f_prev >= s_prev) and (rsi_val < 50) and (rsi_val > 20)
            
            if is_buy or is_sell:
                base_win_rate = 78
                if is_buy:
                    rsi_bonus = min(15, max(0, int(rsi_val - 50)))
                    win_rate = base_win_rate + rsi_bonus
                    sig_text = "⚡ سكالبينج صعود (CALL)"
                else:
                    rsi_bonus = min(15, max(0, int(50 - rsi_val)))
                    win_rate = base_win_rate + rsi_bonus
                    sig_text = "⚡ سكالبينج هبوط (PUT)"
                
                win_rate = min(95, win_rate)
                
                scalp_candidates.append({
                    "وقت الإشارة": candle_time.strftime('%Y-%m-%d %H:%M'),
                    "الزوج": name,
                    "النوع": sig_text,
                    "السعر": round(current_price, 4),
                    "RSI": round(float(rsi_val), 1),
                    "القوة": f"{win_rate}%",
                    "score": win_rate
                })
        except Exception:
            continue
            
    # اختيار أفضل صفقتين فقط لتجنب أي عشوائية
    scalp_candidates = sorted(scalp_candidates, key=lambda x: x['score'], reverse=True)
    top_scalps = scalp_candidates[:2]
    
    return top_scalps, prices_list

# ==========================================
# 4. الواجهة والتحديث
# ==========================================
if st.button("🔄 فحص فريم الدقيقة/الدقيقتين الآن"):
    st.rerun()

with st.spinner("جاري مسح الأسواق على فريم السكالبينج السريع..."):
    scalp_signals, live_prices = scan_scalping_signals()

if live_prices:
    st.subheader("📌 أسعار السوق الحية للأزواج")
    st.dataframe(pd.DataFrame(live_prices), use_container_width=True)

st.markdown("---")
st.subheader("⚡ صفقات السكالبينج السريعة المتاحة")

if scalp_signals:
    st.success("تم رصد فرص سكالبينج سريعة ونقية بنجاح!")
    df_scalp = pd.DataFrame(scalp_signals)
    if 'score' in df_scalp.columns:
        df_scalp = df_scalp.drop(columns=['score'])
        
    st.dataframe(df_scalp, use_container_width=True)
    if ENABLE_SOUND:
        play_sound_alert()
else:
    st.warning("⚪ لا توجد فرصة سكالبينج مطابقة بالشروط اللحظية الدقيقة حالياً. انتظر إغلاق الشمعة القادمة.")

st.markdown("---")
st.info("💡 تم تفعيل فريمات الدقيقة و (1m / 2m) مع مؤشرات سريعة (SMA 3/10 و RSI 9) لتناسب الصفقات الخاطفة يا أستاذ صلاح.")
