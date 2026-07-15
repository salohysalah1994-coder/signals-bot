//@version=5
indicator("Pocket Option Bot - SMC Signals", overlay=true)

// --- إعدادات الحساسية للتداول الآلي ---
len = input.int(3, title="حساسية الفريم الصغير (موصى بـ 3)", minval=1)

// حساب القمم والقيعان السريعة لتحديد مناطق الانعكاس
high_signal = ta.pivothigh(high, len, len)
low_signal  = ta.pivotlow(low, len, len)

var float last_high = na
var float last_low = na

if not na(high_signal)
    last_high := high_signal
if not na(low_signal)
    last_low := low_signal

// شروط الاختراق السريع (CHoCH اللحظي)
bullish_signal = ta.crossover(close, last_high)
bearish_signal = ta.crossunder(close, last_low)

// --- رسم الإشارات على الشارت بصرياً للتأكيد ---
plotshape(bullish_signal, title="BUY_CALL", style=shape.labelup, location=location.belowbar, color=color.green, textcolor=color.white, size=size.small, text="CALL")
plotshape(bearish_signal, title="SELL_PUT", style=shape.labeldown, location=location.abovebar, color=color.red, textcolor=color.white, size=size.small, text="PUT")

// --- التنبيهات بصيغة JSON المتوافقة مع البوت الخاص بك ---
// ملاحظة: يمكنك تعديل مفاتيح الـ JSON بالأسفل لتطابق المتغيرات التي يطلبها الكود الخاص ببوتك (مثل action أو direction)
alertcondition(bullish_signal, title="شراء CALL للبوت", 
     message='{\n  "pair": "{{ticker}}",\n  "action": "BUY",\n  "type": "CALL",\n  "timeframe": "{{interval}}",\n  "price": "{{close}}"\n}')

alertcondition(bearish_signal, title="بيع PUT للبوت", 
     message='{\n  "pair": "{{ticker}}",\n  "action": "SELL",\n  "type": "PUT",\n  "timeframe": "{{interval}}",\n  "price": "{{close}}"\n}')
