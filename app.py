import pandas as pd
import numpy as np

def check_smc_signal(candles_list, swing_length=3):
    """
    تحليل بيانات الشموع لتوليد إشارات شراء (CALL) أو بيع (PUT) بناءً على اختراق القمم والقيعان (SMC/CHoCH).
    :param candles_list: قائمة بالشموع تحتوي على (open, high, low, close)
    :param swing_length: قوة الفلترة لتحديد القمم والقيعان (تتحكم في سرعة الإشارات)
    """
    # تحويل البيانات إلى DataFrame للتعامل معها بسهولة
    df = pd.DataFrame(candles_list)
    if len(df) < (swing_length * 2 + 1):
        return None  # بيانات غير كافية للتحليل
    
    # 1. تحديد القمم والقيعان المحلية (Pivots)
    df['is_high'] = df['high'] == df['high'].rolling(window=swing_length*2+1, center=True).max()
    df['is_low'] = df['low'] == df['low'].rolling(window=swing_length*2+1, center=True).min()
    
    # استخراج قيم آخر قمة وقاع مكتملين
    highs = df[df['is_high']]['high'].values
    lows = df[df['is_low']]['low'].values
    
    if len(highs) < 1 or len(lows) < 1:
        return None
        
    last_swing_high = highs[-1]
    last_swing_low = lows[-1]
    
    # السعر الحالي اللحظي (آخر سعر إغلاق)
    current_price = df['close'].iloc[-1]
    previous_price = df['close'].iloc[-2]
    
    # 2. فحص شروط الاختراق (CHoCH) لتوليد الصفقة
    # إذا اخترق السعر الحالي القمة السابقة صعوداً
    if previous_price <= last_swing_high and current_price > last_swing_high:
        return {
            "signal": "CALL",
            "reason": "Bullish CHoCH (اختراق القمة صعوداً)",
            "price": current_price
        }
        
    # إذا كسر السعر الحالي القاع السابق هبوطاً
    elif previous_price >= last_swing_low and current_price < last_swing_low:
        return {
            "signal": "PUT",
            "reason": "Bearish CHoCH (كسر القاع هبوطاً)",
            "price": current_price
        }
        
    return None # لا توجد إشارة في هذه الشمعة
