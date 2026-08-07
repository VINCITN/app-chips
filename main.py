import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import requests

st.set_page_config(page_title="Crypto & Chip Dashboard", layout="wide")

# Metadati per visualizzazione PWA a tutto schermo su iPhone
st.components.v1.html(
    """
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    """,
    height=0,
)

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
        st.metric(label="Prossimo aggiornamento sicuro tra:", value=f"{secondi_mancanti} secondi")
        st.info("🔄 Lettura da memoria cache di Streamlit.")
    else:
        st.success("🟢 Server pronti per una richiesta diretta!")

    st.markdown("---")
    if st.button("⚡ BYPASS CACHE: Tempo Reale Ora"):
        st.toast("Richiesta immediata dati freschi tramite tunnel protetto.")
        st.cache_data.clear() 
        st.session_state.ultimo_aggiornamento_reale = datetime.now()
        st.rerun()

    st.title("📊 Dashboard Algoritmica Semiconduttori & Geopolitica")
    st.write("Analisi quantitativa unita all'impatto delle politiche USA, EU e Asia.")

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

# --- GENERATORE DI SEGNALI GEOPOLITICI E DI MERCATO ---
def elabora_rating_geopolitico(ticker, rsi, macro_trend, dati_globali):
    trend_global_chip = "positivo" if macro_trend > 0 else "debole"
    
    if ticker == "STM.MI":
        if rsi < 35 and trend_global_chip == "positivo":
            return "🟢 COMPRA", "Le forti correzioni sul settore automotive offrono un punto d'ingresso. Il trend globale dell'AI (Nvidia/TSMC) fa da traino, mitigando i colli di bottiglia normativi dell'Unione Europea."
        elif rsi > 65:
            return "🔴 VENDI", "Titolo in ipercomprato tecnico. Le recenti restrizioni USA sull'export di tecnologie avanzate verso l'Asia e l'aumento dei costi dei materiali pesano sui margini industriali UE."
        else:
            return "🟡 TIENI", "Fase di consolidamento. Equilibrio instabile tra i sussidi dell'EU Chips Act e il rallentamento della supply chain globale dei semiconduttori tradizionali."
            
    elif ticker == "LDO.MI":
        if trend_global_chip == "positivo" and rsi < 55:
            return "🟢 COMPRA", "Il superciclo della difesa globale e l'aumento dei budget militari in Europa proteggono il portafoglio ordini. La solida stabilità produttiva di TSMC garantisce i componenti elettronici critici."
        elif rsi > 75:
            return "🔴 VENDI", "Ipercomprato estremo dettato dalle tensioni geopolitiche già scontate dal mercato. Rischio di stallo se gli USA inaspriscono i controlli ITAR sull'esportazione di microcomponenti."
        else:
            return "🟡 TIENI", "Mantenere in portafoglio. La domanda nel comparto Aerospace & Defence rimane solida, ma i colli di bottiglia negli approvvigionamenti di chip avanzati in Asia suggeriscono cautela."
    
    return "⚖️ NEUTRALE", "Nessuna anomalia macroeconomica rilevata."

# --- TICKERS DI MERCATO ---
TICKERS = {
    "STM.MI": "STMicroelectronics",
    "LDO.MI": "Leonardo S.p.A.",
    "NVDA": "NVIDIA Corp.",
    "TSM": "Taiwan Semiconductor",
    "ASML": "ASML Holding",
    "BTC-USD": "Bitcoin",
}

@st.cache_data(ttl=120)
def scarica_dati(tickers_dict):
    dati_finali = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for ticker in tickers_dict.keys():
        try:
            url = f"https://yahoo.com{ticker}?range=6mo&interval=1d"
            risposta = requests.get(url, headers=headers, timeout=10)
            if risposta.status_code == 200:
                json_data = risposta.json()
                result = json_data["chart"]["result"]
                timestamps = result["timestamp"]
                quotes = result["indicators"]["quote"]
                close_prices = quotes["close"]
                
                dates = [datetime.fromtimestamp(ts).date() for ts in timestamps]
                df_pulito = pd.DataFrame(index=dates)
                df_pulito["Close"] = pd.Series(close_prices, index=dates).astype(float)
                df_pulito.dropna(subset=["Close"], inplace=True)
                
                df_pulito["SMA_20"] = calcola_sma(df_pulito["Close"], 20)
                df_pulito["SMA_50"] = calcola_sma(df_pulito["Close"], 50)
                df_pulito["RSI_14"] = calcola_rsi(df_pulito["Close"], 14)
                
                dati_finali[ticker] = df_pulito
        except Exception:
            pass
    return dati_finali

dati = scarica_dati(TICKERS)

# --- INTERFACCIA PRINCIPALE ---
st.title("💡 Geopolitical & Chip Monitor")

if dati and "STM.MI" in dati and "LDO.MI" in dati:
    # Calcolo trend aggregato dei colossi globali (Nvidia + TSMC + ASML) per l'algoritmo
    try:
        trend_global = (dati["NVDA"]["Close"].pct_change().iloc[-1] + 
                        dati["TSM"]["Close"].pct_change().iloc[-1] + 
                        dati["ASML"]["Close"].pct_change().iloc[-1]) / 3
    except Exception:
        trend_global = 0.0

    # Dati STM
    stm_close = float(dati["STM.MI"]["Close"].iloc[-1])
    stm_var = float(dati["STM.MI"]["Close"].pct_change().iloc[-1] * 100)
    stm_rsi = float(dati["STM.MI"]["RSI_14"].iloc[-1])
    stm_rec, stm_mot = elabora_rating_geopolitico("STM.MI", stm_rsi, trend_global, dati)

    # Dati Leonardo
    ldo_close = float(dati["LDO.MI"]["Close"].iloc[-1])
    ldo_var = float(dati["LDO.MI"]["Close"].pct_change().iloc[-1] * 100)
    ldo_rsi = float(dati["LDO.MI"]["RSI_14"].iloc[-1])
    ldo_rec, ldo_mot = elabora_rating_geopolitico("LDO.MI", ldo_rsi, trend_global, dati)

    # --- RIGA TITOLO: CONFRONTO DIRETTO IN SINTESI (OTTIMIZZATA IPHONE) ---
    st.subheader("⚔️ Focus Italia: Semiconduttori vs Difesa")
    row_col1, row_col2 = st.columns(2)
    
    with row_col1:
        st.markdown(f"### 🇨🇭 STMicroelectronics (`STM.MI`)")
        st.metric(label="Prezzo e Andamento Giornaliero", value=f"{stm_close:.2f} EUR", delta=f"{stm_var:.2f}%")
        st.markdown(f"**Segnale Algoritmico:** `{stm_rec}`")
        st.caption(f"ℹ️ {stm_mot}")
        
    with row_col2:
        st.markdown(f"### 🇮🇹 Leonardo S.p.A. (`LDO.MI`)")
        st.metric(label="Prezzo e Andamento Giornaliero", value=f"{ldo_close:.2f} EUR", delta=f"{ldo_var:.2f}%")
        st.markdown(f"**Segnale Algoritmico:** `{ldo_rec}`")
        st.caption(f"ℹ️ {ldo_mot}")

    st.markdown("---")

    # --- NUOVA SEZIONE: GRAFICO DI CONFRONTO GENERALE (NORMALIZZATO %) ---
    st.subheader("📊 Confronto delle Performance a 6 Mesi (%)")
    st.write("I prezzi sono normalizzati in percentuale per confrontare l'andamento di titoli con valute e valori differenti (Base iniziale = 0%).")
    
    df_confronto = pd.DataFrame()
    # Consideriamo solo i titoli azionari richiesti (escludendo Bitcoin dal benchmark puro dei chip)
    for t_key in ["STM.MI", "LDO.MI", "NVDA", "TSM", "ASML"]:
        if t_key in dati:
            # Calcolo variazione percentuale cumulativa dall'inizio dello storico dei 6 mesi
            prezzo_iniziale = dati[t_key]["Close"].iloc[0]
            df_confronto[TICKERS[t_key]] = ((dati[t_key]["Close"] - prezzo_iniziale) / prezzo_iniziale) * 100
            
    st.line_chart(df_confronto)

    st.markdown("---")
    
    # --- SELEZIONE PER IL GRAFICO SOTTOSTANTE (PRESERVATO ED ASSET SINGOLO) ---
    st.subheader("📈 Analisi Tecnica Dettagliata (Titolo Singolo)")
    asset_scelto = st.selectbox(
        "Scegli quale asset visualizzare sul grafico con Medie Mobili:", 
        options=list(TICKERS.keys()), 
        format_func=lambda x: f"{TICKERS[x]} ({x})"
    )
    
    df_asset = dati[asset_scelto]
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Prezzo Attuale", value=f"{float(df_asset['Close'].iloc[-1]):.2f}", delta=f"{float(df_asset['Close'].pct_change().iloc[-1]*100):.2f}%")
    with m2:
        st.metric(label="RSI (14d)", value=f"{float(df_asset['RSI_14'].iloc[-1]):.2f}")
    with m3:
        current_rsi = float(df_asset['RSI_14'].iloc[-1])
        condizione = "🚨 Ipercomprato" if current_rsi > 70 else "🛒 Ipervenduto" if current_rsi < 30 else "⚖️ Neutrale"
        st.metric(label="Condizione Tecnica", value=condizione)

    st.line_chart(df_asset[["Close", "SMA_20", "SMA_50"]])
    
    with st.expander("📄 Registro Storico Dati (Ultimi 10 giorni)"):
        st.dataframe(df_asset[["Close", "SMA_20", "SMA_50", "RSI_14"]].tail(10))
else:
    st.error("Servizi temporaneamente lenti nel recupero dati da Yahoo Finance. Forza l'aggiornamento dalla barra laterale.")
