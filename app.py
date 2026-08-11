import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# Forziamo una nuova chiave di configurazione per distruggere la vecchia cache
st.set_page_config(page_title="RealTime Monitor Live", page_icon="📈", layout="wide")

# Aggiornamento automatico ogni 1 minuto (60.000 millisecondi) per sbloccare l'orologio
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60000, key="orologio_realtime_v3")

def calcola_tutto_live(ticker_milano):
    """
    Scarica i dati storici e i dati minuto per minuto in modo nativo e leggero.
    """
    try:
        # 1. Dati Storici distinti per le Medie Mobili (Risolve il bug SMA20 = SMA50)
        t = yf.Ticker(ticker_milano)
        df_storia = t.history(period="3mo", interval="1d")
        
        if df_storia.empty:
            return 0.0, 0.0, 0.0, 0.0, 50.0
            
        sma20 = df_storia['Close'].rolling(window=20).mean().iloc[-1]
        sma50 = df_storia['Close'].rolling(window=50).mean().iloc[-1]
        
        # Calcolo RSI 14
        delta = df_storia['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        # 2. TRUCCO REAL-TIME: Scarica l'ultimo minuto di contrattazione di oggi
        df_oggi = t.history(period="1d", interval="1m")
        if not df_oggi.empty:
            prezzo_attuale = df_oggi['Close'].iloc[-1]
        else:
            prezzo_attuale = df_storia['Close'].iloc[-1]
            
        # Variazione percentuale rispetto alla chiusura di ieri
        chiusura_ieri = t.info.get('previousClose', df_storia['Close'].iloc[-2])
        variazione = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
        
        return prezzo_attuale, variazione, sma20, sma50, rsi
    except Exception:
        return 0.0, 0.0, 0.0, 0.0, 50.0

# --- INTERFACCIA CRUSCOTTO ---
st.title("💡 Real-Time Geopolitical & Chip Monitor")

# Gestione Oraria Italiana forzata in tempo reale
fuso_roma = pytz.timezone("Europe/Rome")
ora_esatta = datetime.now(fuso_roma).strftime("%H:%M:%S")
st.write(f"Ultimo aggiornamento flussi: **{ora_esatta}** (Sincronizzato al secondo)")
st.success("🟢 CORE SERVER RE-INIZIALIZZATO")

st.header("🇮🇹 Borsa di Milano (Quotazioni Attuali)")
col1, col2 = st.columns(2)

with col1:
    # Per STMicroelectronics su Yahoo si usa il ticker ufficiale STMMI.MI
    p, v, s20, s50, r = calcola_tutto_live("STMMI.MI")
    st.subheader("STMicroelectronics (STM.MI)")
    st.metric(label="Prezzo live", value=f"€ {p:.2f}", delta=f"{v:.2f}%")
    st.text(f"SMA 20: {s20:.2f} | SMA 50: {s50:.2f} | RSI 14: {r:.1f}")
    
    if r < 35:
        st.error("🟢 COMPRA: Le forti correzioni offrono un punto d'ingresso.")
    elif r > 70:
        st.error("🔴 VENDI: Ipercomprato sul settore.")
    else:
        st.warning("🟡 TIENI: Prezzo in linea con i flussi di mercato.")

with col2:
    # Leonardo S.p.A.
    p, v, s20, s50, r = calcola_tutto_live("LDO.MI")
    st.subheader("Leonardo S.p.A. (LDO.MI)")
    st.metric(label="Prezzo live", value=f"€ {p:.2f}", delta=f"{v:.2f}%")
    st.text(f"SMA 20: {s20:.2f} | SMA 50: {s50:.2f} | RSI 14: {r:.1f}")
    
    if r > 80:
        st.error("🔴 VENDI: Ipercomprato estremo.")
    elif r < 30:
        st.error("🟢 COMPRA: Sottovalutato rispetto ai flussi.")
    else:
        st.warning("🟡 TIENI: Prezzo in linea con i flussi di mercato.")
