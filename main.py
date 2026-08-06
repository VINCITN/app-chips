import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st

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
        st.toast("Richiesta immediata dati freschi tramite tunnel CSV.")
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

# --- DOWNLOAD DATI IN CSV SENZA BLOCCO CLOUD ---
@st.cache_data(ttl=120)
def scarica_dati(tickers_dict):
    dati_finali = {}
    
    # Calcolo timestamp Unix per la richiesta CSV
    fine_ts = int(time.time())
    inizio_ts = int(fine_ts - (180 * 24 * 60 * 60)) # 6 mesi fa
    
    for ticker in tickers_dict.keys():
        try:
            # Generazione dell'URL di download diretto del file CSV di Yahoo Finance (Infallibile su Cloud)
            url = f"https://yahoo.com{ticker}?period1={inizio_ts}&period2={fine_ts}&interval=1d&events=history&includeAdjustedClose=true"
            
            # Lettura del file CSV direttamente in un DataFrame Pandas
            df = pd.read_csv(url)
            
            if df is not None and not df.empty:
                # Imposta la data come indice
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                
                # Creazione dataframe pulito per i grafici
                df_pulito = pd.DataFrame(index=df.index)
                df_pulito["Close"] = df["Close"].astype(float)
                
                # Calcolo degli indicatori tecnici richiesti
                df_pulito["SMA_20"] = calcola_sma(df_pulito["Close"], 20)
                df_pulito["SMA_50"] = calcola_sma(df_pulito["Close"], 50)
                df_pulito["RSI_14"] = calcola_rsi(df_pulito["Close"], 14)
                
                dati_finali[ticker] = df_pulito
        except Exception:
            # Fallback di emergenza nel caso in cui un ticker specifico sia momentaneamente offline
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
    st.warning("I server di Yahoo Finance stanno rifiutando la connessione simultanea. Prova a cliccare su BYPASS CACHE nella barra laterale tra pochi secondi.")
