import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

def get_secret(key):
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, "")

st.set_page_config(
    page_title="OKX Web3 DEX Trading Bot", 
    page_icon="🤖", 
    layout="wide"
)

# --- OKX DEX API Functions ---
def get_okx_quote(chain_id, from_token, to_token, amount):
    """جلب أفضل سعر ومسار تداول من OKX Aggregator"""
    url = "https://www.okx.com/api/v5/dex/aggregator/quote"
    headers = {
        "OK-ACCESS-KEY": get_secret("OKX_API_KEY"),
        "OK-ACCESS-PASSPHRASE": get_secret("OKX_PASSPHRASE"),
        "Content-Type": "application/json"
    }
    params = {
        "chainId": chain_id,
        "amount": str(amount),
        "fromTokenAddress": from_token,
        "toTokenAddress": to_token
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

# --- UI Interface ---
st.title("🤖 OKX Web3 DEX Trading Bot")
st.caption("بوت التداول الآلي وربط الإشارات لشبكتي BNB Chain و Solana")

# شريط الإعدادات الجانبي
st.sidebar.header("⚙️ إعدادات الشبكة والخدمة")
network = st.sidebar.selectbox("اختر الشبكة المستهدفة", ["BNB Chain (56)", "Solana (501)"])

# تخصيص العنوان حسب الشبكة المختارة
if "BNB" in network:
    chain_id = "56"
    default_from = "0x55d398326f99059ff775485246999027b3197955"  # USDT BSC
    default_to = "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82"    # CAKE
else:
    chain_id = "501"
    default_from = "So11111111111111111111111111111111111111112" # SOL
    default_to = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC

# واجهة إدخال الأوامر
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 إعدادات صفقة التبادل (Swap)")
    from_token = st.text_input("عنوان عملة البيع (From Token Address)", default_from)
    to_token = st.text_input("عنوان عملة الشراء (To Token Address)", default_to)
    amount = st.text_input("الكمية (بالوحدات الصغرى Decimal Amount)", "1000000")
    
    btn_fetch = st.button("📊 جلب أفضل تسعير ومسار (Quote)", use_container_width=True)

with col2:
    st.subheader("📡 نتيجة استجابة OKX API")
    if btn_fetch:
        with st.spinner("جاري الاتصال بـ OKX DEX Aggregator..."):
            quote_data = get_okx_quote(chain_id, from_token, to_token, amount)
            
            if quote_data.get("code") == "0" and quote_data.get("data"):
                st.success("تم جلب المسار بنجاح!")
                data = quote_data["data"][0]
                
                # عرض تفاصيل التسعير
                st.metric(label="مبلغ الشراء المتوقع (To Amount)", value=data.get("toTokenAmount", "N/A"))
                st.json(data)
            else:
                st.error("حدث خطأ في جلب التسعير:")
                st.json(quote_data)

st.divider()
st.info("💡 ملاحظة: الخطوة التالية هي إضافة مفاتيح OKX Secrets وربط منفذ تنفيذ الصفقات عبر التوقيع التلقائي.")
