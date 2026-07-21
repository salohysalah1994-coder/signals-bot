//@version=5
indicator("Pocket Option 3M Strategy - EMA & RSI", overlay=true)

// --- 1. إعدادات المؤشرات ---
emaFastLen = input.int(9, title="سريع Fast EMA")
emaSlowLen = input.int(21, title="بطيء Slow EMA")
rsiLen     = input.int(14, title="فترة RSI")

// --- 2. حساب المؤشرات ---
emaFast = ta.ema(close, emaFastLen)
emaSlow = ta.ema(close, emaSlowLen)
rsiVal  = ta.rsi(close, rsiLen)

// رسم المتوسطات على الرسم البياني
plot(emaFast, title="EMA Fast (9)", color=color.green, linewidth=2)
plot(emaSlow, title="EMA Slow (21)", color=color.red, linewidth=2)

// --- 3. شروط الصفقات ---
// تقاطع EMA الأخضر فوق الأحمر + RSI أعلى من 50
buyCondition  = ta.crossover(emaFast, emaSlow) and (rsiVal > 50)

// تقاطع EMA الأخضر تحت الأحمر + RSI أسفل من 50
sellCondition = ta.crossunder(emaFast, emaSlow) and (rsiVal < 50)

// --- 4. إشارات الصفقات على الشارت ---
plotshape(series=buyCondition, title="إشارة شراء (CALL / HIGHER)", style=shape.triangleup, 
          location=location.belowbar, color=color.green, size=size.small, text="CALL 3M")

plotshape(series=sellCondition, title="إشارة بيع (PUT / LOWER)", style=shape.triangledown, 
          location=location.abovebar, color=color.red, size=size.small, text="PUT 3M")
