import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import time

# ==========================================
# 1. إعدادات البوت والاستراتيجية
# ==========================================
SYMBOL = "EURUSD=X"      # الزوج المراد تداوله (أو أي زوج آخر مثل GBPUSD=X)
TIMEFRAME = "5m"         # الفريم: 1m لصفقات دقيقتين، أو 5m لصفقات 5-15 دقيقة
AO_FAST = 1
AO_SLOW = 34
SIGNAL_WMA = 5
TREND_EMA = 200          # فلتر الاتجاه العام
RSI_PERIOD = 14          # فلتر التشبع


def fetch_and_analyze_data(symbol, timeframe):
    # جلب بيانات السعر للحظات الأخيرة
    df = yf.download(tickers=symbol, period="5d", interval=timeframe, progress=False)
    
    # معالجة بيانات Columns لمنع أي التعارضات في Pandas
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # --------------------------------------
    # 2. حساب مؤشر GO Strategy (Awesome Oscillator)
    # --------------------------------------
    df['sma_fast'] = ta.sma(df['Close'], length=AO_FAST)
    df['sma_slow'] = ta.sma(df['Close'], length=AO_SLOW)
    df['buffer1'] = df['sma_fast'] - df['sma_slow']
    df['buffer2'] = ta.wma(df['buffer1'], length=SIGNAL_WMA)

    # --------------------------------------
    # 3. الفلاتر إضافية لزيادة قوة الاستراتيجية
    # --------------------------------------
    # فلتر 1: اتجاه الترند العام (EMA 200)
    df['ema_200'] = ta.ema(df['Close'], length=TREND_EMA)
    
    # فلتر 2: قوة الزخم والتشبع (RSI 14)
    df['rsi'] = ta.rsi(df['Close'], length=RSI_PERIOD)

    # --------------------------------------
    # 4. الشروط الصارمة للدخول في الصفقات
    # --------------------------------------
    # التقاطعات الأساسية لمؤشر GO
    cross_up = (df['buffer1'] > df['buffer2']) & (df['buffer1'].shift(1) <= df['buffer2'].shift(1))
    cross_down = (df['buffer1'] < df['buffer2']) & (df['buffer1'].shift(1) >= df['buffer2'].shift(1))

    # صفقة شراء (CALL): تقاطع صاعد + السعر فوق EMA200 + RSI غير مشبع بالشراء (< 70)
    df['CALL'] = cross_up & (df['Close'] > df['ema_200']) & (df['rsi'] < 70)

    # صفقة بيع (PUT): تقاطع هابط + السعر تحت EMA200 + RSI غير مشبع بالبيع (> 30)
    df['PUT'] = cross_down & (df['Close'] < df['ema_200']) & (df['rsi'] > 30)

    return df

# ==========================================
# 5. حلقة التشغيل الفعلي والتنبيهات للحظية
# ==========================================
print(f"--- بدء تشغيل بوت التداول المطور على زوج {SYMBOL} ---")

while True:
    try:
        data = fetch_and_analyze_data(SYMBOL, TIMEFRAME)
        last_candle = data.iloc[-1]
        previous_candle = data.iloc[-2]
        
        current_time = last_candle.name
        close_price = round(float(last_candle['Close']), 5)
        
        # التأكد من إشارة الشمعة المغلقة حديثاً
        if previous_candle['CALL']:
            print(f"\n[🚀 إشارة شراء قوية - CALL] | الوقت: {current_time} | السعر: {close_price}")
            print("--> التوصية: ادخل صفقة صعود (CALL) مدتها 2 إلى 3 شمعات.")
            # هنا يمكنك إضافة كود تنفيذ الصفقة التلقائي عبر الـ API
            
        elif previous_candle['PUT']:
            print(f"\n[🔻 إشارة بيع قوية - PUT] | الوقت: {current_time} | السعر: {close_price}")
            print("--> التوصية: ادخل صفقة هبوط (PUT) مدتها 2 إلى 3 شمعات.")
            # هنا يمكنك إضافة كود تنفيذ الصفقة التلقائي عبر الـ API
            
        else:
            print(f"لا توجد إشارة حاسمة حتى الآن... | السعر الحالي: {close_price}", end="\r")

        # انتظار 10 ثوان قبل الفحص التالي
        time.sleep(10)

    except Exception as e:
        print(f"\nحدث خطأ أثناء جلب البيانات: {e}")
        time.sleep(15)
