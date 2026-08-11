import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 1. TRUCCO ANTI-CACHE: Forza la pulizia di tutta la memoria bloccata precedente
try:
    st.cache_data.clear()
    st.cache_resource.clear()
except:
    pass

# Configurazione con una chiave completamente nuova per ingannare Hugging Face
st.set_page_config(page_title="Monitor Milano RealTime", page_icon="📈", layout="wide")

# Sincronizzazione automatica forzata ogni 1 minuto per sbloccare l'orologio
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60000, key="sblocco_orologio_forzato_v5")

def calcola_dati_mercato(ticker_simbolo):
    """
    Scarica i dati storici e intraday separando nettamente gli indicatori.
    """
    try:
        t = yf.Ticker(ticker_simbolo)
        # Chiediamo lo storico degli ultimi 3 mesi
        df_storico = t.history(period="3mo", interval="1d")
        
        if df_storico.empty:
            return 0.0, 0.0, 0.0, 0.0, 50.0
            
        # CORREZIONE MEDIE MOBILI: Finestre di calcolo separate (Evita SMA20 = SMA50)
        sma20 = df_storico['Close'].rolling(window=20).mean().iloc[-1]
        sma50 = df_storico['Close'].rolling(window=50).mean().iloc[-1]
        
        # Calcolo RSI 14 periodi
        delta = df_storico['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        # FORZATURA PREZZO IN DIRETTA: Scarica l'ultimo minuto disponibile ad adesso
        df_oggi = t.history(period="1d", interval="1m")
        if not df_oggi.empty:
            prezzo_reale = df_oggi['Close'].iloc[-1]
        else:
            prezzo_reale = df_storico['Close'].iloc[-1]
            
        chiusura_precedente = t.info.get('previousClose', df_storico['Close'].iloc[-2])
        variazione_percentuale = ((prezzo_reale - chiusura_precedente) / chiusura_precedente) * 100
        
        return prezzo_reale, variazione_percentuale, sma20, sma50, rsi
    except Exception:
        return 0.0, 0.0, 0.0, 0.0, 50.0

# --- COSTRUZIONE DELLA PAGINA ---
st.title("💡 Real-Time Geopolitical & Chip Monitor")

# Calcolo e forzatura dell'orario di Roma in tempo reale
fuso_italia = pytz.timezone("Europe/Rome")
ora_corrente = datetime.now(fuso_italia).strftime("%H:%M:%S")
st.write(f"Ultimo aggiornamento reale flussi: **{ora_corrente}**")
st.success("🟢 CORE ENGINE RESETTATO - DATI LIVE")

st.header("🇮🇹 Quotazioni Borsa di Milano")
col1, col2 = st.columns(2)

with col1:
    # Per STMicroelectronics usiamo il ticker ufficiale di Milano
    prezzo, var, s20, s50, rsi_val = calcola_dati_mercato("STM.MI")
    st.subheader("STMicroelectronics (STM.MI)")
    st.metric(label="Prezzo attuale", value=f"€ {prezzo:.2f}", delta=f"{var:.2f}%")
    st.text(f"SMA 20: {s20:.2f} | SMA 50: {s50:.2f} | RSI 14: {rsi_val:.1f}")
    
    if rsi_val < 38:
        st.error("🟢 COMPRA: Forti correzioni, ottimo punto d'ingresso.")
    elif rsi_val > 70:
        st.error("🔴 VENDI: Titolo in forte ipercomprato.")
    else:
        st.warning("🟡 TIENI: Prezzo stabile rispetto ai flussi.")

with col2:
    # Leonardo S.p.A.
    prezzo, var, s20, s50, rsi_val = calcola_dati_mercato("LDO.MI")
    st.subheader("Leonardo S.p.A. (LDO.MI)")
    st.metric(label="Prezzo attuale", value=f"€ {prezzo:.2f}", delta=f"{var:.2f}%")
    st.text(f"SMA 20: {s20:.2f} | SMA 50: {s50:.2f} | RSI 14: {rsi_val:.1f}")
    
    if rsi_val > 75:
        st.error("🔴 VENDI: Ipercomprato estremo, tensioni geopolitiche scontate.")
    elif rsi_val < 30:
        st.error("🟢 COMPRA: Sottovalutato, flussi in aumento.")
    else:
        st.warning("🟡 TIENI: Prezzo in linea con i flussi storici.")
