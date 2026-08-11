import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

def ottieni_prezzo_realtime_milano(ticker):
    """
    Estrae il prezzo in tempo reale da fonti pubbliche per aggirare il ritardo di 15 minuti.
    """
    # Mappatura dei ticker sui codici ISIN o ID del Sole 24 Ore
    # STM (STMicroelectronics): IT0000226229 o id stm
    # LDO (Leonardo): IT0003856405
    
    url_mappa = {
        "STM.MI": "https://ilsole24ore.com",
        "LDO.MI": "https://ilsole24ore.com"
    }
    
    if ticker not in url_mappa:
        # Se non è Milano, usa un fallback generico o mantieni il calcolo classico
        return None
        
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        risposta = requests.get(url_mappa[ticker], headers=headers, timeout=10)
        soup = BeautifulSoup(risposta.text, 'html.parser')
        
        # Cerca la classe CSS che contiene l'ultimo prezzo sul Sole 24 Ore
        # Nota: La classe esatta dipende dalla struttura del sito. In alternativa si usa Finanza Repubblica o Milano Finanza.
        elemento_prezzo = soup.find("span", {"class": "v-price"}) # Esempio di selettore
        elemento_variazione = soup.find("span", {"class": "v-chg"})
        
        prezzo = float(elemento_prezzo.text.replace(",", ".").strip())
        variazione = float(elemento_variazione.text.replace(",", ".").replace("%", "").strip())
        
        return prezzo, variazione
    except Exception as e:
        print(f"Errore scraping realtime per {ticker}: {e}")
        return None, None

def calcola_indicatori_corretti(ticker_symbol):
    """
    Risolve il bug delle medie mobili uguali e unisce il prezzo in tempo reale.
    """
    import yfinance as yf # Usato SOLO per lo storico delle medie mobili, non per il prezzo di oggi
    
    # 1. Scarica lo storico (i dati passati di Yahoo vanno bene per le medie mobili)
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="3mo", interval="1d")
    
    if df.empty:
        return None

    # CORREZIONE BUG MEDIE MOBILI (Finestre temporali differenti e distinte)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # Calcolo RSI 14 corretto
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9) # Evita divisione per zero
    df['RSI14'] = 100 - (100 / (1 + rs))
    
    # 2. Prendi il prezzo IN TEMPO REALE SENZA RITARDO dallo scraping
    prezzo_oggi, variazione_oggi = ottieni_prezzo_realtime_milano(ticker_symbol)
    
    # Fallback nel caso il sito di scraping sia momentaneamente irraggiungibile
    if prezzo_oggi is None:
        prezzo_oggi = df['Close'].iloc[-1]
        variazione_oggi = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100

    return {
        "prezzo": prezzo_oggi,
        "variazione": variazione_oggi,
        "sma20": df['SMA20'].iloc[-1],
        "sma50": df['SMA50'].iloc[-1],
        "rsi": df['RSI14'].iloc[-1]
    }
