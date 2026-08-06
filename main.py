from datetime import datetime, timedelta
import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# --- CONFIGURAZIONE CACHE E SICUREZZA ---
if "ultimo_aggiornamento_reale" not in st.session_state:
    st.session_state.ultimo_aggiornamento_reale = (
        datetime.now() - timedelta(minutes=5)
    )

st.set_page_config(page_title="Crypto & Chip Dashboard", layout="wide")

# --- BARRA LATERALE CON TIMER E CONTROLLO ---
with st.sidebar:
    st.header("⏱️ Stato Connessione API")
    ora_attuale = datetime.now()
    secondi_passati = (
        ora_attuale - st.session_state.ultimo_aggiornamento_reale
    ).total_seconds()
    secondi_mancanti = max(0, int(120 - secondi_passati))

    if secondi_mancanti > 0:
        st.metric(
            label="Prossimo aggiornamento sicuro tra:",
            value=f"{secondi_mancanti} secondi",
        )
        st.info("🔄 Lettura automatica da memoria cache di Streamlit.")
    else:
        st.success("🟢 Server pronti per una richiesta diretta!")

    st.markdown("---")
    if st.button("⚡ BYPASS CACHE: Tempo Reale Ora"):
        st.toast("Richiesta immediata dati freschi a Yahoo Finance.")
        st.cache_data.clear() # Svuota la cache nativa di Streamlit
        st.session_state.ultimo_aggiornamento_reale = datetime.now()
        st.rerun()

    st.title("📊 Dashboard Algoritmica Semiconduttori & Geopolitica")
    st.write(
        "Incrocio dati di mercato, indicatori di analisi tecnica e impatto delle politiche USA-Asia."
    )

# --- FUNZIONI DI CALCOLO MATEMATICO ---
def calcola_sma(series, window):
    return series.rolling(window=window).mean()

def calcola_rsi(series, window=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    avg_loss = avg_loss.replace(0, 0.00001)
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# --- TICKERS DI MERCATO ---
TICKERS = {
    "STM.MI": "STMicroelectronics (Milano)",
    "NVDA": "NVIDIA Corporation",
    "TSM": "Taiwan Semiconductor Mfg.",
    "ASML": "ASML Holding",
    "BTC-USD": "Bitcoin",
}

# --- DOWNLOAD DATI ---
@st.cache_data(ttl=120) # Gestisce la cache in modo nativo e sicuro
def scarica_dati(tickers_dict):
    dati_finali = {}
    for ticker, nome in tickers_dict.items():
        try:
            # Rimosso il parametro session= obsoleto
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period="6m")
            if not df.empty:
                df["SMA_20"] = calcola_sma(df["Close"], 20)
                df["SMA_50"] = calcola_sma(df["Close"], 50)
                df["RSI_14"] = calcola_rsi(df["Close"], 14)
                dati_finali[ticker] = df
        except Exception as e:
            st.error(f"Errore nello scaricamento di {ticker}: {e}")
    return dati_finali

dati = scarica_dati(TICKERS)

# --- INTERFACCIA PRINCIPALE ---
st.title("💡 Analisi Algoritmica Semiconduttori e Crypto")

if dati:
    asset_scelto = st.selectbox(
        "Seleziona un titolo o una crypto da analizzare:", 
        options=list(TICKERS.keys()), 
        format_func=lambda x: f"{TICKERS[x]} ({x})"
    )
    
    df_asset = dati[asset_scelto]
    ultimo_prezzo = df_asset["Close"].iloc[-1]
    variazione = df_asset["Close"].pct_change().iloc[-1] * 100
    ultimo_rsi = df_asset["RSI_14"].iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Ultimo Prezzo di Chiusura", value=f"{ultimo_prezzo:.2f}", delta=f"{variazione:.2f}%")
    with col2:
        st.metric(label="RSI (14 giorni)", value=f"{ultimo_rsi:.2f}")
    with col3:
        if ultimo_rsi > 70:
            stato = "🚨 Ipercomprato (Rischio Correzione)"
        elif ultimo_rsi < 30:
            stato = "🛒 Ipervenduto (Opportunità)"
        else:
            stato = "⚖️ Neutrale"
        st.metric(label="Condizione Tecnica", value=stato)
        
    st.markdown("---")
    
    st.subheader(f"📈 Andamento Prezzi e Medie Mobili per {TICKERS[asset_scelto]}")
    grafico_df = df_asset[["Close", "SMA_20", "SMA_50"]]
    st.line_chart(grafico_df)
    
    with st.expander("📄 Visualizza ultimi dati storici"):
        st.dataframe(df_asset[["Close", "SMA_20", "SMA_50", "RSI_14"]].tail(10))
else:
    st.warning("Impossibile caricare i dati di mercato. Verifica la connessione o il bypass della cache.")
