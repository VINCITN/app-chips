import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 1. COMANDO DI EMERGENZA: Distrugge la vecchia memoria bloccata delle 13:09
try:
    st.cache_data.clear()
    st.cache_resource.clear()
except:
    pass

# Cambiamo il nome interno per costringere il server a ricaricare tutto da zero
st.set_page_config(page_title="Monitor Flussi RealTime V8", page_icon="📊", layout="wide")

# Forza l'aggiornamento automatico della pagina ogni 1 minuto
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60000, key="orologio_anti_blocco_v8")

def calcola_dati_live(ticker_simbolo):
    try:
        t = yf.Ticker(ticker_simbolo)
        
        # Scarica lo storico per calcolare le medie separate (Risolve SMA20 = SMA50)
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
        
        # TRUCCO REAL-TIME: Scarica i dati al minuto per saltare il ritardo di Yahoo
        df_oggi = t.history(period="1d", interval="1m")
        if not df_oggi.empty:
            prezzo_attuale = df_oggi['Close'].iloc[-1]
        else:
            prezzo_attuale = df_storia['Close'].iloc[-1]
            
        chiusura_ieri = t.info.get('previousClose', df_storia['Close'].iloc[-2])
        variazione = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
        
        return prezzo_attuale, variazione, sma20, sma50, rsi
    except:
        return 0.0, 0.0, 0.0, 0.0, 50.0

# --- INTERFACCIA CRUSCOTTO ---
st.title("💡 Real-Time Geopolitical & Chip Monitor")

# Sincronizzazione Ora Italiana di questo istante
fuso_roma = pytz.timezone("Europe/Rome")
ora_esatta = datetime.now(fuso_roma).strftime("%H:%M:%S")
st.write(f"Ultimo aggiornamento flussi: **{ora_esatta}** (Sincronizzato live)")
st.success("🟢 SERVER AGGIORNATO - NUOVO FLUSSO ATTIVO")

st.header("🇮🇹 Borsa di Milano (Quotazioni in Diretta)")
col1, col2 = st.columns(2)

with col1:
    p, v, s20, s50, r = calcola_dati_live("STMMI.MI")  # Ticker ufficiale Milano
    st.subheader("STMicroelectronics (STM.MI)")
    st.metric(label="Prezzo attuale", value=f"€ {p:.2f}", delta=f"{v:.2f}%")
    st.text(f"SMA 20: {s20:.2f} | SMA 50: {s50:.2f} | RSI 14: {r:.1f}")
    
    if r < 35: st.error("🟢 COMPRA: Punto d'ingresso ottimale.")
    elif r > 70: st.error("🔴 VENDI: Ipercomprato.")
    else: st.warning("🟡 TIENI")

with col2:
    p, v, s20, s50, r = calcola_dati_live("LDO.MI")
    st.subheader("Leonardo S.p.A. (LDO.MI)")
    st.metric(label="Prezzo attuale", value=f"€ {p:.2f}", delta=f"{v:.2f}%")
    st.text(f"SMA 20: {s20:.2f} | SMA 50: {s50:.2f} | RSI 14: {r:.1f}")
    
    if r > 80: st.error("🔴 VENDI: Ipercomprato estremo.")
    elif r < 30: st.error("🟢 COMPRA")
    else: st.warning("🟡 TIENI")
