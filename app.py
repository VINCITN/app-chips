import time
import pandas as pd
import requests
import streamlit as st

# Configurazione Mobile-First ottimizzata per lo schermo dell'iPhone
st.set_page_config(
    page_title="AI Quant Mobile", page_icon="📱", layout="centered"
)

# Stile grafico personalizzato in modalità scura (stile iOS)
st.markdown(
    """
    <style>
    .reportview-container .main .block-container{ max-width: 100%; padding-top: 1rem; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 15px; border: 1px solid #333; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 24px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📱 AI Quant Trading")
st.caption("Monitoraggio Filiera Chip Globale H24")

# Sostituisci il testo tra le virgolette con la tua chiave Alpha Vantage reale
ALPHA_VANTAGE_KEY = "IL_TUO_API_KEY_QUI"

# Elenco dei produttori e venditori mondiali di semiconduttori
CHIP_TICKERS = {
    "NVDA": "NVIDIA",
    "TSM": "TSMC",
    "ASML": "ASML",
    "INF": "Infineon",
    "NXPI": "NXP",
    "TXN": "Texas Inst.",
    "AMD": "AMD",
    "INTC": "Intel",
}

# Pesi percentuali attribuiti a ciascuna società nell'algoritmo
WEIGHTS = {
    "NVDA": 0.30,
    "TSM": 0.25,
    "ASML": 0.15,
    "INF": 0.10,
    "NXPI": 0.08,
    "TXN": 0.05,
    "AMD": 0.05,
    "INTC": 0.02,
}


def get_live_data(ticker, api_key):
    """Estrazione dati in tempo reale dai mercati finanziari globali."""
    url = f"https://alphavantage.co{ticker}&apikey={api_key}"
    try:
        res = requests.get(url).json().get("Global Quote", {})
        return float(res.get("10. change percent", "0.0%").replace("%", ""))
    except:
        return 0.0


# Pulsante per avviare il calcolo in tempo reale
if st.button("🔄 AGGIORNA PREVISIONI ORA", use_container_width=True):
    if ALPHA_VANTAGE_KEY == "23US5COJVCUTVQXK":
        st.error(
            "⚠️ Inserisci la tua chiave API di Alpha Vantage nel codice per scaricare i dati."
        )
    else:
        with st.spinner("Interrogando i mercati mondiali in tempo reale..."):
            changes = {}
            for i, ticker in enumerate(CHIP_TICKERS.keys()):
                changes[ticker] = get_live_data(ticker, ALPHA_VANTAGE_KEY)
                # Pausa tecnica per non sovraccaricare il server del piano gratuito
                if (i + 1) % 4 == 0:
                    time.sleep(12)

            # Scarica i dati di STM quotata a Wall Street per anticipare i movimenti di Milano
            stm_live = get_live_data("STM", ALPHA_VANTAGE_KEY)

            # Calcolo dell'Indice di Impulso Globale Semiconduttori
            global_index = sum(
                changes[t] * WEIGHTS[t] for t in CHIP_TICKERS.keys()
            )

            # Algoritmo decisionale quantitativo H24 per STM e Leonardo
            score_stm = (0.6 * global_index) + (0.4 * stm_live)
            score_leo = (0.3 * global_index) + (0.7 * (global_index * 0.8))

            def determina_segnale(score):
                if score > 0.8:
                    return "🟢 COMPRA", "#00cc66"
                elif score < -0.8:
                    return "🔴 VENDI", "#ff3333"
                return "🟡 TIENI", "#ffcc00"

            sig_stm, col_stm = determina_segnale(score_stm)
            sig_leo, col_leo = determina_segnale(score_leo)

            # --- SCHEDA TARGET 1: STM ---
            st.markdown("---")
            st.markdown("### **STMicroelectronics (STM)**")
            st.markdown(
                f"<h2 style='color:{col_stm}; margin-top:0;'>{sig_stm}</h2>",
                unsafe_allow_html=True,
            )

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Impatto Chip", f"{global_index:.2f}%")
            with col_m2:
                st.metric("Previsione Titolo", f"{score_stm:.2f}%")

            # --- SCHEDA TARGET 2: LEONARDO ---
            st.markdown("---")
            st.markdown("### **Leonardo S.p.A. (LDO)**")
            st.markdown(
                f"<h2 style='color:{col_leo}; margin-top:0;'>{sig_leo}</h2>",
                unsafe_allow_html=True,
            )

            col_m3, col_m4 = st.columns(2)
            with col_m3:
                st.metric("Spinta Difesa", f"{(global_index*0.8):.2f}%")
            with col_m4:
                st.metric("Previsione Titolo", f"{score_leo:.2f}%")

            # --- DETTAGLIO MONITORAGGIO FUSI ORARI ---
            st.markdown("---")
            st.markdown("### 🌍 Focus Borse Attive")
            st.write(f"**Impulso Asia (TSMC):** {changes['TSM']:.2f}%")
            st.write(
                f"**Impulso Europa (ASML/INF):** {((changes['ASML']+changes['INF'])/2):.2f}%"
            )
            st.write(f"**Impulso America (NVIDIA):** {changes['NVDA']:.2f}%")
