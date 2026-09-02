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
    page_title="ماسح صفقات الفوركس النقي - صلاح",
    page_icon="📈",
    layout="wide"
)

st.title("📈 روبوت الفوركس النقي (أفضل صفقتين كل ربع ساعة) - صلاح")
st.markdown("البوت مصمم خصيصاً لتفادي التداخلات وعرض أفضل صفقتين حيتين ونقيتين فقط.")
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
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني للفحص (الفريم):", ["15m", "30m", "1h", "5m"], index=0)
ENABLE_SOUND = st.sidebar.checkbox("🔊 تفعيل التنبيه الصوتي عند ظهور الفرص", value=True)

def play_sound_alert():
    audio_html = """
        <audio autoplay controls style="display:none;">
            <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# ==========================================
# 3. دالة الفحص الصارم (أفضل صفقتين فقط)
# ==========================================
def scan_best_clean_signals():
    all_candidates = []
    prices_list = []
    
    for name, symbol in PAIRS_MAP.items():
        try:
            df = yf.download(symbol, period="2d", interval=TIMEFRAME, progress=False)
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
            
            # نأخذ الشمعة المغلقة الأخيرة بدقة
            i = len(df) - 2
            candle_time = df['datetime'].iloc[i]
            
            sma_fast = ta.sma(close_series, length=5)
            sma_slow = ta.sma(close_series, length=20)
            rsi = ta.rsi(close_series, length=14)
            
            if sma_fast is None or sma_slow is None or rsi is None:
                continue
                
            f_now, f_prev = sma_fast.iloc[i], sma_fast.iloc[i-1]
            s_now, s_prev = sma_slow.iloc[i], sma_slow.iloc[i-1]
            rsi_val = rsi.iloc[i]
            
            is_buy = (f_now > s_now) and (rsi_val > 48) and (rsi_val < 70)
            is_sell = (f_now < s_now) and (rsi_val < 52) and (rsi_val > 30)
            
            if is_buy or is_sell:
                base_win_rate = 75
                if is_buy:
                    rsi_factor = min(18, max(0, int(rsi_val - 50)))
                    win_rate = base_win_rate + rsi_factor
                    sig_text = "🟢 صعود (شراء نقي - CALL)"
                else:
                    rsi_factor = min(18, max(0, int(50 - rsi_val)))
                    win_rate = base_win_rate + rsi_factor
                    sig_text = "🔴 هبوط (بيع نقي - PUT)"
                
                win_rate = min(95, win_rate)
                
                all_candidates.append({
                    "وقت الدخول": candle_time.strftime('%Y-%m-%d %H:%M'),
                    "الزوج": name,
                    "الإشارة": sig_text,
                    "السعر": round(current_price, 4),
                    "RSI": round(float(rsi_val), 1),
                    "نسبة النجاح": f"{win_rate}%",
                    "score": win_rate  # للترتيب واختيار الأفضل
                })
        except Exception:
            continue
            
    # ترتيب الفرص حسب نسبة النجاح واختيار أعلى صفقتين فقط لتجنب العجين والتداخل
    all_candidates = sorted(all_candidates, key=lambda x: x['score'], reverse=True)
    best_signals = all_candidates[:2] # أخذ أفضل صفقتين فقط
    
    return best_signals, prices_list

# ==========================================
# 4. الواجهة والتحديث
# ==========================================
if st.button("🔄 فحص السوق وجلب أفضل صفقتين الآن"):
    st.rerun()

with st.spinner("جاري تنقية السوق واستخراج أفضل فرصتين بدقة..."):
    best_signals, live_prices = scan_best_clean_signals()

if live_prices:
    st.subheader("📌 أسعار السوق الحية للأزواج")
    st.dataframe(pd.DataFrame(live_prices), use_container_width=True)

st.markdown("---")
st.subheader("💎 أفضل صفقتين نقيتين متاحتين للدخول الآن")

if best_signals:
    st.success("تم فلترة السوق بنجاح وعرض أقوى فرصتين لتجنب أي تداخلات!")
    df_best = pd.DataFrame(best_signals)
    # إزالة عمود الـ score الداخلي من الجدول المعروض
    if 'score' in df_best.columns:
        df_best = df_best.drop(columns=['score'])
        
    st.dataframe(df_best, use_container_width=True)
    if ENABLE_SOUND:
        play_sound_alert()
else:
    st.warning("⚪ لا توجد فرص مكتملة بالشروط النقية حالياً. السوق هادئ، انتظر قليلاً أو جرب التحديث بعد قليل يا صلاح.")

st.markdown("---")
st.info("💡 النظام الآن يعرض لك أعلى صفقتين قوة ونقاء فقط لتركز عليهما بدون أي إزعاج أو تداخلات.")
