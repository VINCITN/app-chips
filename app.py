import streamlit as str_lt  # Questa è la libreria Streamlit per la grafica
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup

# 1. Configurazione della pagina Hugging Face
str_lt.set_page_config(page_title="Geopolitical & Chip Monitor", page_icon="💡", layout="wide")

# Auto-aggiornamento ogni 5 minuti (300.000 millisecondi)
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=300000, key="datarefresh")

# 2. Funzione per estrarre i prezzi IN DIRETTA da Milano (Senza ritardo di Yahoo)
def prendi_prezzo_realtime_milano(isin, ticker_fallback):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        # Scraping da Il Sole 24 Ore per dati istantanei di Piazza Affari
        url = f"https://ilsole24ore.com{isin}"
        risposta = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(risposta.text, 'html.parser')
        
        # Estrazione dati reali dal sito finanziario
        prezzo_testo = soup.find("span", {"class": "v-price"}).text
        var_testo = soup.find("span", {"class": "v-chg"}).text
        
        prezzo = float(prezzo_testo.replace(".", "").replace(",", ".").strip())
        variazione = float(var_testo.replace("%", "").replace(",", ".").strip())
        return prezzo, variazione
    except Exception:
        # Se lo scraping fallisce, usa Yahoo Finance come paracadute
        t = yf.Ticker(ticker_fallback)
        df_oggi = t.history(period="1d", interval="1m")
        if not df_oggi.empty:
            return df_oggi['Close'].iloc[-1], ((df_oggi['Close'].iloc[-1] - t.info.get('previousClose', df_oggi['Close'].iloc[-1])) / t.info.get('previousClose', 1)) * 100
        return 0.0, 0.0

# 3. Funzione per calcolare gli indicatori (Risolve il bug delle medie uguali)
def calcola_indicatori(ticker_storico):
    ticker = yf.Ticker(ticker_storico)
    df = ticker.history(period="3mo", interval="1d") # Scarica 3 mesi per la SMA 50
    if df.empty:
        return 0.0, 0.0, 50.0
    
    # CORREZIONE BUG: finestre di calcolo separate
    sma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    sma50 = df['Close'].rolling(window=50).mean().iloc[-1]
    
    # Calcolo RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    
    return sma20, sma50, rsi

# 4. Interfaccia Grafica del Report
str_lt.title("💡 Real-Time Geopolitical & Chip Monitor")

# Gestione Orario Italiano Corretto
fuso_roma = pytz.timezone("Europe/Rome")
ora_esatta = datetime.now(fuso_roma).strftime("%H:%M:%S")
str_lt.write(f"Ultimo aggiornamento flussi: **{ora_esatta}** (Aggiornato ogni 5 min automaticamente)")
str_lt.success("🟢 SERVER DATI ATTIVO")

# --- TITOLI DI MILANO (IN TEMPO REALE) ---
str_lt.header("🇮🇹 Borsa di Milano (Real-Time)")
col1, col2 = str_lt.columns(2)

with col1:
    # STMicroelectronics (ISIN: IT0000226229)
    prezzo, variazione = prendi_prezzo_realtime_milano("IT0000226229", "STM.MI")
    sma20, sma50, rsi = calcola_indicatori("STM.MI")
    
    str_lt.subheader("STMicroelectronics (STM.MI)")
    str_lt.metric(label="Prezzo attuale", value=f"€ {prezzo:.2f}", delta=f"{variazione:.2f}%")
    str_lt.text(f"SMA 20: {sma20:.2f} | SMA 50: {sma50:.2f} | RSI 14: {rsi:.1f}")
    
    # Logica Segnale
    if rsi < 35:
        str_lt.error("🟢 COMPRA: Le forti correzioni offrono un punto d'ingresso.")
    elif rsi > 70:
        str_lt.error("🔴 VENDI: Ipercomprato sul settore.")
    else:
        str_lt.warning("🟡 TIENI: Prezzo in linea con i flussi di mercato.")

with col2:
    # Leonardo S.p.A. (ISIN: IT0003856405)
    prezzo, variazione = prendi_prezzo_realtime_milano("IT0003856405", "LDO.MI")
    sma20, sma50, rsi = calcola_indicatori("LDO.MI")
    
    str_lt.subheader("Leonardo S.p.A. (LDO.MI)")
    str_lt.metric(label="Prezzo attuale", value=f"€ {prezzo:.2f}", delta=f"{variazione:.2f}%")
    str_lt.text(f"SMA 20: {sma20:.2f} | SMA 50: {sma50:.2f} | RSI 14: {rsi:.1f}")
    
    # Logica Segnale
    if rsi > 80:
        str_lt.error("🔴 VENDI: Ipercomprato estremo dettato dalle tensioni geopolitiche.")
    elif rsi < 30:
        str_lt.error("🟢 COMPRA: Sottovalutato rispetto ai flussi.")
    else:
        str_lt.warning("🟡 TIENI: Prezzo in linea con i flussi di mercato.")
