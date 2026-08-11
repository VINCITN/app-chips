import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup

# Configurazione della pagina Hugging Face
st.set_page_config(page_title="Geopolitical & Chip Monitor", page_icon="💡", layout="wide")

# Aggiornamento automatico della pagina ogni 5 minuti (300000 millisecondi)
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=300000, key="datarefresh")

# Funzione Scraping dal Sole 24 Ore per evitare il ritardo di Yahoo Finance
def prendi_prezzo_realtime_milano(url_sole, ticker_fallback):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        # Legge i dati in diretta dai mercati del Sole 24 Ore
        risposta = requests.get(url_sole, headers=headers, timeout=5)
        soup = BeautifulSoup(risposta.text, 'html.parser')
        
        # Estrae i dati real-time
        prezzo_testo = soup.find("span", {"class": "v-price"}).text
        var_testo = soup.find("span", {"class": "v-chg"}).text
        
        prezzo = float(prezzo_testo.replace(".", "").replace(",", ".").strip())
        variazione = float(var_testo.replace("%", "").replace(",", ".").strip())
        return prezzo, variazione
    except Exception:
        # Paracadute: se lo scraping ha problemi temporanei, usa Yahoo Finance
        t = yf.Ticker(ticker_fallback)
        df_oggi = t.history(period="1d", interval="1m")
        if not df_oggi.empty:
            p = df_oggi['Close'].iloc[-1]
            v = ((p - t.info.get('previousClose', p)) / t.info.get('previousClose', 1)) * 100
            return p, v
        return 0.0, 0.0

# Calcolo degli indicatori storici (Risolto il bug delle medie uguali)
def calcola_indicatori(ticker_storico):
    ticker = yf.Ticker(ticker_storico)
    df = ticker.history(period="3mo", interval="1d") # Carica 3 mesi per calcolare la SMA 50
    if df.empty:
        return 0.0, 0.0, 50.0
    
    # FINESTRE SEPARATE: Risolve il problema SMA20 = SMA50
    sma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    sma50 = df['Close'].rolling(window=50).mean().iloc[-1]
    
    # Calcolo RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    
    return sma20, sma50, rsi

# --- INTERFACCIA ---
st.title("💡 Real-Time Geopolitical & Chip Monitor")

# Fuso orario italiano
fuso_roma = pytz.timezone("Europe/Rome")
ora_esatta = datetime.now(fuso_roma).strftime("%H:%M:%S")
st.write(f"Ultimo aggiornamento flussi: **{ora_esatta}** (Aggiornato ogni 5 min automaticamente)")
st.success("🟢 SERVER DATI ATTIVO")

st.header("🇮🇹 Borsa di Milano (Real-Time)")
col1, col2 = st.columns(2)

with col1:
    # STMicroelectronics
    url_stm = "https://mercati.ilsole24ore.com/azioni/borsa-italiana/dettaglio-completo/STMMI.MI"
    prezzo, variazione = prendi_prezzo_realtime_milano(url_stm, "STM.MI")
    sma20, sma50, rsi = calcola_indicatori("STM.MI")
    
    st.subheader("STMicroelectronics (STM.MI)")
    st.metric(label="Prezzo attuale", value=f"€ {prezzo:.2f}", delta=f"{variazione:.2f}%")
    st.text(f"SMA 20: {sma20:.2f} | SMA 50: {sma50:.2f} | RSI 14: {rsi:.1f}")
    
    if rsi < 35:
        st.error("🟢 COMPRA: Le forti correzioni offrono un punto d'ingresso.")
    elif rsi > 70:
        st.error("🔴 VENDI: Ipercomprato sul settore.")
    else:
        st.warning("🟡 TIENI: Prezzo in linea con i flussi di mercato.")

with col2:
    # Leonardo S.p.A.
    url_ldo = "https://ilsole24ore.com"
    prezzo, variazione = prendi_prezzo_realtime_milano(url_ldo, "LDO.MI")
    sma20, sma50, rsi = calcola_indicatori("LDO.MI")
    
    st.subheader("Leonardo S.p.A. (LDO.MI)")
    st.metric(label="Prezzo attuale", value=f"€ {prezzo:.2f}", delta=f"{variazione:.2f}%")
    st.text(f"SMA 20: {sma20:.2f} | SMA 50: {sma50:.2f} | RSI 14: {rsi:.1f}")
    
    if rsi > 80:
        st.error("🔴 VENDI: Ipercomprato estremo dettato dalle tensioni geopolitiche.")
    elif rsi < 30:
        st.error("🟢 COMPRA: Sottovalutato rispetto ai flussi.")
    else:
        st.warning("🟡 TIENI: Prezzo in linea con i flussi di mercato.")
