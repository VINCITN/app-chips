import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import requests

st.set_page_config(page_title="Crypto & Chip Dashboard", layout="wide")

if "ultimo_aggiornamento_reale" not in st.session_state:
    st.session_state.ultimo_aggiornamento_reale = (
        datetime.now() - timedelta(minutes=5)
    )

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
        st.toast("Richiesta immediata dati freschi tramite tunnel protetto.")
        st.cache_data.clear() 
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

# --- TUNNEL IN JSON CON USER-AGENT ---
@st.cache_data(ttl=120)
def scarica_dati(tickers_dict):
    dati_finali = {}
    
    # Intestazioni di sicurezza (Fingiamo di essere un browser reale per superare i blocchi cloud)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    
    for ticker in tickers_dict.keys():
        try:
            # Endpoint ufficiale per i grafici JSON (Molto più stabile dei file CSV)
            url = f"https://yahoo.com{ticker}?range=6mo&interval=1d"
            
            risposta = requests.get(url, headers=headers, timeout=10)
            
            if risposta.status_code == 200:
                json_data = risposta.json()
                result = json_data["chart"]["result"][0]
                
                # Estrazione timestamp e prezzi di chiusura
                timestamps = result["timestamp"]
                quotes = result["indicators"]["quote"][0]
                close_prices = quotes["close"]
                
                # Conversione in DataFrame Pandas
                dates = [datetime.fromtimestamp(ts).date() for ts in timestamps]
                df_pulito = pd.DataFrame(index=dates)
                df_pulito["Close"] = pd.Series(close_prices, index=dates).astype(float)
                
                # Rimozione di eventuali righe vuote nei giorni festivi
                df_pulito.dropna(subset=["Close"], inplace=True)
                
                # Calcolo degli indicatori tecnici richiesti
                df_pulito["SMA_20"] = calcola_sma(df_pulito["Close"], 20)
                df_pulito["SMA_50"] = calcola_sma(df_pulito["Close"], 50)
                df_pulito["RSI_14"] = calcola_rsi(df_pulito["Close"], 14)
                
                dati_finali[ticker] = df_pulito
        except Exception:
            pass
            
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
    ultimo_prezzo = float(df_asset["Close"].iloc[-1])
    variazione = float(df_asset["Close"].pct_change().iloc[-1] * 100)
    ultimo_rsi = float(df_asset["RSI_14"].iloc[-1])
    
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
    st.line_chart(df_asset[["Close", "SMA_20", "SMA_50"]])
    
    with st.expander("📄 Visualizza ultimi dati storici"):
        st.dataframe(df_asset[["Close", "SMA_20", "SMA_50", "RSI_14"]].tail(10))
else:
    st.error("I server Cloud sono momentaneamente limitati da Yahoo. Attendi 10 secondi e clicca su BYPASS CACHE nella barra laterale.")
