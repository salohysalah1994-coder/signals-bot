import streamlit as st
import requests
import json
import os
import base64
from dotenv import load_dotenv

# مكتبات شبكة BNB (EVM)
from web3 import Web3

# مكتبات شبكة Solana
from solana.rpc.api import Client as SolanaClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

# تحميل البيانات السرية (من البيئة المحلية أو من Streamlit Secrets)
load_dotenv()

def get_secret(key):
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, "")

# ضبط إعدادات الصفحة
st.set_page_config(page_title="OKX DEX Multi-Chain Bot", page_icon="🤖", layout="wide")

# --- الإعدادات الثابتة وروابط الـ RPC ---
BSC_RPC = "https://bsc-dataseed.binance.org/"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"

# --- دالة التفاعل مع OKX DEX API ---
def get_okx_swap_tx(chain_id, from_token, to_token, amount, wallet_address, slippage="0.5"):
    """جلب بيانات الصفقة الجاهزة للتوقيع من OKX DEX"""
    url = "https://www.okx.com/api/v5/dex/aggregator/swap"
    
    headers = {
        "OK-ACCESS-KEY": get_secret("OKX_API_KEY"),
        "OK-ACCESS-PASSPHRASE": get_secret("OKX_PASSPHRASE"),
        "Content-Type": "application/json"
    }
    
    params = {
        "chainId": chain_id,
        "amount": str(amount),
        "fromTokenAddress": from_token,
        "toTokenAddress": to_token,
        "userWalletAddress": wallet_address,
        "slippage": slippage
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        res_data = response.json()
        
        if res_data.get("code") == "0" and len(res_data.get("data", [])) > 0:
            return res_data["data"][0]
        else:
            st.error(f"خطأ من OKX API: {res_data.get('msg', 'تعذر جلب بيانات الصفقة')}")
            return None
    except Exception as e:
        st.error(f"حدث خطأ أثناء الاتصال بـ OKX API: {e}")
        return None

# --- دالة توقيع وتنفيذ صفقة BNB (EVM) ---
def execute_evm_swap(tx_data, private_key):
    try:
        w3 = Web3(Web3.HTTPProvider(BSC_RPC))
        account = w3.eth.account.from_key(private_key)
        
        # تجهيز المعاملة
        transaction = {
            'to': w3.to_checksum_address(tx_data['to']),
            'value': int(tx_data['value']),
            'data': tx_data['data'],
            'gas': int(tx_data['gas']),
            'gasPrice': int(tx_data['gasPrice']),
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': 56
        }
        
        # التوقيع والإرسال
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return w3.to_hex(tx_hash)
    except Exception as e:
        st.error(f"فشل تنفيذ صفقة BNB: {e}")
        return None

# --- دالة توقيع وتنفيذ صفقة Solana ---
def execute_solana_swap(raw_tx_data, private_key_bs58):
    try:
        sol_client = SolanaClient(SOLANA_RPC)
        keypair = Keypair.from_base58_string(private_key_bs58)
        
        # فك تشفير المعاملة
        tx_bytes = base64.b64decode(raw_tx_data)
        versioned_tx = VersionedTransaction.from_bytes(tx_bytes)
        
        # إرسال المعاملة الموقعة
        result = sol_client.send_transaction(versioned_tx)
        return str(result.value)
    except Exception as e:
        st.error(f"فشل تنفيذ صفقة Solana: {e}")
        return None

# --- الواجهة الرئيسية (Streamlit UI) ---
st.title("🤖 لوحة تحكم بوت التداول - OKX DEX Aggregator")
st.caption("دعم شبكتي BNB Chain و Solana")

st.sidebar.header("⚙️ إعدادات الشبكة والخدمات")
network_choice = st.sidebar.selectbox("اختر الشبكة للتداول", ["BNB Chain (BSC)", "Solana (SOL)"])
slippage_input = st.sidebar.slider("الانزلاق السعري (Slippage %)", 0.1, 5.0, 0.5)

# تحديد معرف الشبكة وقيم الافتراضية للعملات
if network_choice == "BNB Chain (BSC)":
    chain_id = "56"
    default_from = "0x55d398326f99059ff775485246999027b3197955"  # USDT BSC
    default_to = "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82"    # CAKE BSC
    decimals = 18
else:
    chain_id = "501"
    default_from = "So11111111111111111111111111111111111111112" # Native SOL
    default_to = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC Solana
    decimals = 9

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 تفاصيل الصفقة")
    from_token = st.text_input("عنوان العملة المراد بيعها (From Token)", default_from)
    to_token = st.text_input("عنوان العملة المراد شاؤها (To Token)", default_to)
    amount_human = st.number_input("الكمية المراد تداولها", min_value=0.0001, value=1.0, format="%.4f")
    wallet_address = st.text_input("عنوان محفظتك (Wallet Address)", "")

with col2:
    st.subheader("📊 الفحص والتنفيذ")
    
    # حساب الكمية حسب الدقة (Decimals)
    raw_amount = int(amount_human * (10 ** decimals))
    
    if st.button("1. جلب مسار الصفقة والأسعار من OKX"):
        if not wallet_address:
            st.warning("يرجى إدخال عنوان محفظتك أولاً.")
        else:
            with st.spinner("جاري جلب المسار من OKX..."):
                swap_info = get_okx_swap_tx(chain_id, from_token, to_token, raw_amount, wallet_address, str(slippage_input))
                if swap_info:
                    st.success("تم جلب البيانات بنجاح!")
                    st.session_state['current_swap_tx'] = swap_info['tx']
                    st.json(swap_info.get('routerResult', {}))

    if 'current_swap_tx' in st.session_state:
        st.write("---")
        if st.button("🚨 2. تأكيد وتنفيذ الصفقة آلياً", type="primary"):
            with st.spinner("جاري توقيع الصفقة وإرسالها للشبكة..."):
                if network_choice == "BNB Chain (BSC)":
                    pk = get_secret("EVM_PRIVATE_KEY")
                    tx_hash = execute_evm_swap(st.session_state['current_swap_tx'], pk)
                    if tx_hash:
                        st.success(f"تم تنفيذ الصفقة بنجاح! رقم المعاملة: {tx_hash}")
                        st.markdown(f"[عرض المعاملة على BscScan](https://bscscan.com/tx/{tx_hash})")
                else:
                    pk = get_secret("SOL_PRIVATE_KEY")
                    tx_hash = execute_solana_swap(st.session_state['current_swap_tx']['data'], pk)
                    if tx_hash:
                        st.success(f"تم تنفيذ الصفقة بنجاح! رقم المعاملة: {tx_hash}")
                        st.markdown(f"[عرض المعاملة على Solscan](https://solscan.io/tx/{tx_hash})")
