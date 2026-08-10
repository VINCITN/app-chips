import pandas as pd
import yfinance as yf
import json
from datetime import datetime
import os

TICKERS = {
    "STM": "STMicroelectronics",
    "LDO.MI": "Leonardo S.p.A.",
    "NVDA": "NVIDIA Corp.",
    "TSM": "Taiwan Semiconductor",
    "ASML": "ASML Holding",
    "BTC-USD": "Bitcoin"
}

def calcola_sma(series, window):
    # Calcola la Media Mobile Semplice evitando i valori vuoti (NaN)
    return series.rolling(window=window).mean()

def calcola_rsi(series, window=14):
    # Calcola l'RSI matematico reale basato sulle variazioni di prezzo
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean().replace(0, 0.00001)
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def elabora_rating_geopolitico(ticker, rsi, macro_trend):
    trend_global_chip = "positivo" if macro_trend > 0 else "debole"
    
    if ticker == "STM":
        if rsi < 35 and trend_global_chip == "positivo":
            return "🟢 COMPRA", "Le forti correzioni sul settore automotive offrono un punto d'ingresso. Il trend globale dell'AI fa da traino."
        elif rsi > 65:
            return "🔴 VENDI", "Titolo in ipercomprato tecnico. Le restrizioni USA sull'export pesano sui margini UE."
        else:
            return "🟡 TIENI", "Fase di consolidamento. Equilibrio instabile tra i sussidi dell'EU Chips Act e il rallentamento della supply chain."
            
    elif ticker == "LDO.MI":
        if trend_global_chip == "positivo" and rsi < 55:
            return "🟢 COMPRA", "Il superciclo della difesa globale e l'aumento dei budget militari in Europa proteggono il portafoglio ordini."
        elif rsi > 75:
            return "🔴 VENDI", "Ipercomprato estremo dettato dalle tensioni geopolitiche già scontate dal mercato."
        else:
            return "🟡 TIENI", "Mantenere in portafoglio. La domanda nel comparto Aerospace & Defence rimane solida."
            
    # Regole di salvataggio generali per gli altri titoli (NVDA, TSM, ASML, BTC)
    if rsi < 30:
        return "🟢 COMPRA", "Forte ipervenduto tecnico. Opportunità di accumulo sul settore semiconduttori/crypto."
    elif rsi > 70:
        return "🔴 VENDI", "Ipercomprato di breve termine. Possibili prese di beneficio imminenti."
    else:
        return "🟡 TIENI", "Prezzo in linea con i flussi di mercato attuali. Nessun eccesso tecnico."

def main():
    struttura_analisi = {}
    macro_trend_generale = 1.0 # Parametro fittizio impostato come positivo per l'algoritmo
    
    print("Inizio download dati storici da Yahoo Finance...")
    
    for ticker, nome in TICKERS.items():
        try:
            # Scarica 60 giorni di dati giornalieri per calcolare correttamente la SMA 50 e l'RSI
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            
            if not df.empty and len(df) >= 50:
                # Applica le funzioni matematiche sulla colonna dei prezzi di chiusura
                df['SMA20'] = calcola_sma(df['Close'], window=20)
                df['SMA50'] = calcola_sma(df['Close'], window=50)
                df['RSI14'] = calcola_rsi(df['Close'], window=14)
                
                # Estrai l'ultimo valore valido calcolato (l'ultima riga del DataFrame)
                ultima_sma20 = float(df['SMA20'].iloc[-1])
                ultima_sma50 = float(df['SMA50'].iloc[-1])
                ultimo_rsi = float(df['RSI14'].iloc[-1])
                
                # Elabora il segnale operativo basato sulle regole geopolitiche e sull'RSI
                segnale, motivazione = elabora_rating_geopolitico(ticker, ultimo_rsi, macro_trend_generale)
                
                # Inserisci i dati formattati nella struttura del JSON
                struttura_analisi[ticker] = {
                    "sma20": f"{ultima_sma20:.2f}",
                    "sma50": f"{ultima_sma50:.2f}",
                    "rsi": f"{ultimo_rsi:.1f}",
                    "segnale": segnale,
                    "motivazione": motivazione
                }
                print(f"✅ Analisi completata con successo per: {ticker}")
            else:
                print(f"⚠️ Dati insufficienti per {ticker}. Genero dati di fallback.")
                struttura_analisi[ticker] = {"sma20": "N/D", "sma50": "N/D", "rsi": "50.0", "segnale": "⚖️ NEUTRALE", "motivazione": "Dati storici non disponibili."}
                
        except Exception as e:
            print(f"❌ Errore durante l'elaborazione di {ticker}: {e}")
            struttura_analisi[ticker] = {"sma20": "Err", "sma50": "Err", "rsi": "50.0", "segnale": "⚖️ NEUTRALE", "motivazione": "Errore nel calcolo dei dati."}

    # Costruisci il payload JSON finale
    output_finale = {
        "ultimo_aggiornamento_algoritmo": datetime.now().strftime("%H:%M:%S"),
        "analisi": struttura_analisi
    }
    
    # Scrivi e salva il file (verrà letto dall'index.html sul server statico)
    with open("analisi.json", "w", encoding="utf-8") as f:
        json.dump(output_finale, f, indent=4, ensure_ascii=False)
        
    print("🎉 File 'analisi.json' generato e salvato correttamente!")

if __name__ == "__main__":
    main()
