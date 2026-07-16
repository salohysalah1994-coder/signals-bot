import streamlit as st
import pandas as pd
import numpy as np
import ta
import time
import json
import threading
import websocket

# ==========================================
# أولاً: كود الـ API المطور لاستقبال البث الحقيقي
# ==========================================
class PocketOptionAPI:
    def __init__(self, ssid):
        self.ssid = ssid
        self.url = "wss://api-eu.po.market/socket.io/?EIO=4&transport=websocket"
        self.ws = None
        self.connected = False
        self.ticks = [] # لتخزين الأسعار القادمة فورياً

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        
        t = threading.Thread(target=self.ws.run_forever)
        t.daemon = True
        t.start()

    def on_open(self, ws):
        self.connected = True
        # تسجيل الدخول بالـ SSID
        auth_message = f'40{{"token":"{self.ssid}"}}'
        self.ws.send(auth_message)

    def subscribe_to_asset(self, asset):
        # الاشتراك في السعر المباشر للزوج المختار
        if self.connected and self.ws:
            sub_message = f'42{{"action":"subscribe","asset":"{asset}"}}'
            try:
                self.ws.send(sub_message)
            except Exception:
                pass

    def on_message(self, ws, message):
        try:
            # تنظيف الرسائل القادمة من السوكيت وقراءة الأسعار
            if message.startswith("42"):
                data = json.loads(message[2:])
                if isinstance(data, list) and len(data) > 1:
                    price_info = data[1]
                    if 'price' in price_info:
                        self.ticks.append(float(price_info['price']))
                        # الاحتفاظ بآخر 100 حركة سعر فقط للتحليل
                        if len(self.ticks) > 100:
                            self.ticks.pop(0)
        except Exception:
            pass

    def on_error(self, ws, error):
        pass

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False

    def open_order(self, asset, amount, direction, duration=60):
        if not self.connected or not self.ws:
            return False
            
        order_data = {
            "action": "openOrder",
            "data": {
                "asset": asset,
                "amount": amount,
                "action": direction,      # "call" (شراء) أو "put" (بيع)
                "duration": duration,     # بالثواني
                "isDemo": True            # ديمو (تجريبي)
            }
        }
        
        payload = f'42{json.dumps(order_data)}'
        try:
            self.ws.send(payload)
            return True
        except Exception:
            return False

# ==========================================
# ثانياً: واجهة مستخدم التطبيق (Streamlit App)
# ==========================================
st.set_page_config(page_title="Pocket Option Auto-Trader", layout="wide")
st.title("🤖 Pocket Option Auto-Trader (Real-time Demo)")

try:
    SSID = st.secrets["SSID"]
except Exception:
    st.error("⚠️ لم يتم العثور على رمز SSID في إعدادات Secrets!")
    st.stop()

@st.cache_resource
def get_api_connection(ssid):
    api = PocketOptionAPI(ssid)
    api.connect()
    # تأمين وقت للاتصال الأولي
    time.sleep(2)
    return api

st.info("🔄 جاري الاتصال المباشر وقراءة حركة السوق...")
api = get_api_connection(SSID)

# واجهة التحكم
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚙️ إعدادات التداول")
    asset = st.selectbox("اختر زوج العملات الحقيقي:", ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD"])
    trade_amount = st.number_input("مبلغ الصفقة ($):", min_value=1, value=10)
    trade_duration = st.number_input("مدة الصفقة بالثواني:", min_value=30, value=60)
    auto_trade_enabled = st.toggle("تفعيل التداول التلقائي الفوري ⚡")

# تفعيل الاشتراك بالزوج فور تحديده
api.subscribe_to_asset(asset)

with col2:
    st.subheader("📊 حركة الأسعار المباشرة")
    status_placeholder = st.empty()
    
    # التحقق من استقبال بيانات الأسعار الفعلية
    if len(api.ticks) > 10:
        status_placeholder.success(f"✅ متصل ويتم استقبال أسعار {asset} الحية بنجاح!")
    else:
        status_placeholder.warning("⏳ جاري استقبال نبضات الأسعار الأولى من المنصة (تأكد من فتح سوق العملة حالياً)...")

# استخدام الأسعار الحقيقية للتحليل
if len(api.ticks) > 15:
    df = pd.DataFrame({'close': api.ticks})
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    current_rsi = df['rsi'].iloc[-1]
    
    st.divider()
    st.subheader("📢 العمليات المباشرة وإشارات السوق")
    
    # عرض الرسم البياني الحقيقي
    st.line_chart(df['close'])
    
    if auto_trade_enabled:
        if current_rsi < 30:
            st.success(f"🟢 إشارة شراء حقيقية (RSI: {current_rsi:.2f})")
            success = api.open_order(asset, trade_amount, "call", trade_duration)
            if success:
                st.toast("🚀 تم تنفيذ صفقة شراء (CALL) على حساب الديمو!")
        elif current_rsi > 70:
            st.error(f"🔴 إشارة بيع حقيقية (RSI: {current_rsi:.2f})")
            success = api.open_order(asset, trade_amount, "put", trade_duration)
            if success:
                st.toast("🚀 تم تنفيذ صفقة بيع (PUT) على حساب الديمو!")
        else:
            st.warning(f"🟡 نراقب السعر الحالي... مؤشر RSI في منطقة آمنة: {current_rsi:.2f}")
else:
    # حماية للواجهة عند بداية التشغيل
    st.info("💡 بانتظار تجميع ما يكفي من حركات السعر الحية لحساب المؤشرات (تستغرق عادةً 10-20 ثانية)...")
