import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# دالة آمنة لجلب وقراءة المفاتيح بدون رموز عربية أو مسافات خفية
def get_clean_secret(key):
    val = ""
    if key in st.secrets:
        val = str(st.secrets[key])
    else:
        val = str(os.getenv(key, ""))
    # إزالة الأسطر الجديدة والمسافات والرموز التي تسبب خطأ latin-1
    return val.encode('ascii', 'ignore').decode('ascii').strip()

st.set_page_config(
    page_title="OKX Web3 DEX Trading Bot", 
    page_icon="🤖", 
    layout="wide"
)

st.title("🤖 OKX Web3 DEX Trading Bot")
st.caption("نظام التداول والربط التلقائي عبر OKX DEX Aggregator")

# --- Sidebar Configuration ---
st.sidebar.header("⚙️ إعدادات الحساب والشبكة")
network = st.sidebar.selectbox("اختر الشبكة المستهدفة", ["BNB Chain (56)", "Solana (501)"])

api_key = get_clean_secret("OKX_API_KEY")
if not api_key:
    st.sidebar.warning("⚠️ لم يتم ضبط مفاتيح Secrets بعد في Streamlit!")
else:
    st.sidebar.success("✅ مفاتيح OKX Secrets متصلة")

if "BNB" in network:
    chain_id = "56"
    default_from = "0x55d398326f99059ff775485246999027b3197955"  # USDT BSC
    default_to = "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82"    # CAKE
else:
    chain_id = "501"
    default_from = "So11111111111111111111111111111111111111112" # SOL
    default_to = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC

# --- OKX API Core Request Function ---
def okx_request(endpoint, params=None):
    url = f"https://www.okx.com{endpoint}"
    
    headers = {
        "OK-ACCESS-KEY": get_clean_secret("OKX_API_KEY"),
        "OK-ACCESS-PASSPHRASE": get_clean_secret("OKX_PASSPHRASE"),
        "Content-Type": "application/json"
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_quote(chain, from_tok, to_tok, amt):
    endpoint = "/api/v5/dex/aggregator/quote"
    params = {
        "chainId": chain,
        "amount": str(amt),
        "fromTokenAddress": from_tok,
        "toTokenAddress": to_tok
    }
    return okx_request(endpoint, params)

def build_swap_tx(chain, from_tok, to_tok, amt, user_wallet, slippage="0.5"):
    endpoint = "/api/v5/dex/aggregator/swap"
    params = {
        "chainId": chain,
        "amount": str(amt),
        "fromTokenAddress": from_tok,
        "toTokenAddress": to_tok,
        "userWalletAddress": user_wallet,
        "slippage": slippage
    }
    return okx_request(endpoint, params)

# --- Main UI Tabs ---
tab1, tab2 = st.tabs(["📊 فحص السعر والمسار (Quote)", "⚡ تنفيذ التبادل (Swap Build)"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 إدخال البيانات")
        from_token = st.text_input("عنوان عملة البيع", default_from, key="q_from")
        to_token = st.text_input("عنوان عملة الشراء", default_to, key="q_to")
        amount = st.text_input("الكمية (بالوحدات الصغرى)", "1000000", key="q_amt")
        btn_quote = st.button("📊 جلب التسعير والمسار", use_container_width=True)

    with col2:
        st.subheader("📡 استجابة التسعير")
        if btn_quote:
            with st.spinner("جاري التواصل مع OKX..."):
                res = get_quote(chain_id, from_token, to_token, amount)
                if res.get("code") == "0" and res.get("data"):
                    st.success("تم جلب التسعير بنجاح!")
                    st.metric("الكمية المتوقعة للوصول", res["data"][0].get("toTokenAmount", "0"))
                    st.json(res["data"][0])
                else:
                    st.error("فشل جلب التسعير:")
                    st.json(res)

with tab2:
    st.subheader("🛠️ تجهيز معاملة التبادل والتوقيع")
    wallet_addr = st.text_input("عنوان محفظتك (Your Wallet Address)", placeholder="أدخل عنوان محفظتك هنا")
    slippage = st.slider("نسبة الانزلاق المسموح (Slippage %)", 0.1, 5.0, 0.5)
    
    if st.button("🚀 بناء بيانات الترانزاكشن (Build Swap Tx)", use_container_width=True):
        if not wallet_addr:
            st.warning("يرجى إدخال عنوان المحفظة أولاً!")
        else:
            with st.spinner("جاري إعداد صفقة التداول مع OKX Aggregator..."):
                tx_res = build_swap_tx(chain_id, from_token, to_token, amount, wallet_addr, str(slippage))
                if tx_res.get("code") == "0" and tx_res.get("data"):
                    st.success("تم بناء المعاملة بنجاح وجاهزة للتوقيع!")
                    st.json(tx_res["data"][0])
                else:
                    st.error("خطأ في إعداد المعاملة:")
                    st.json(tx_res)
