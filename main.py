import pandas as pd
import yfinance as yf
import json
from datetime import datetime
import os

TICKERS = {
    "STM.MI": "STMicroelectronics",
    "LDO.MI": "Leonardo S.p.A.",
    "NVDA": "NVIDIA Corp.",
    "TSM": "Taiwan Semiconductor",
    "ASML": "ASML Holding",
    "BTC-USD": "Bitcoin"
}

def calcola_sma(series, window):
    return series.rolling(window=window).mean()

def calcola_rsi(series, window=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean().replace(0, 0.00001)
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def elabora_rating_geopolitico(ticker, rsi):
    if ticker == "STM":
        if rsi < 35: return "🟢 COMPRA", "Le forti correzioni sul settore automotive offrono un punto d'ingresso."
        elif rsi > 65: return "🔴 VENDI", "Titolo in ipercomprato tecnico. Restrizioni export USA pesano sui margini."
        else: return "🟡 TIENI", "Fase di consolidamento. Equilibrio instabile tra EU Chips Act e supply chain."
    elif ticker == "LDO.MI":
        if rsi < 55: return "🟢 COMPRA", "Il superciclo della difesa globale e l'aumento dei budget UE proteggono gli ordini."
        elif rsi > 75: return "🔴 VENDI", "Ipercomprato estremo dettato dalle tensioni geopolitiche già scontate."
        else: return "🟡 TIENI", "Mantenere in portafoglio. La domanda nel comparto Aerospace & Defence rimane solida."
    if rsi < 30: return "🟢 COMPRA", "Forte ipervenduto tecnico. Opportunità di accumulo di lungo periodo."
    elif rsi > 70: return "🔴 VENDI", "Ipercomprato di breve termine. Possibili prese di beneficio."
    return "🟡 TIENI", "Prezzo in linea con i flussi di mercato attuali. Nessun eccesso."

def main():
    struttura_analisi = {}
    print("Avvio estrazione dati centralizzata su server...")
    
    for ticker, nome in TICKERS.items():
        try:
            # Scarica lo storico per gli indicatori
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            
            # Scarica il prezzo real-time più recente (candela a 1 minuto dell'ultimo giorno)
            df_live = yf.download(ticker, period="1d", interval="1m", progress=False)
            
            if not df.empty and len(df) >= 50:
                df['SMA20'] = calcola_sma(df['Close'], window=20)
                df['SMA50'] = calcola_sma(df['Close'], window=50)
                df['RSI14'] = calcola_rsi(df['Close'], window=14)
                
                # Prendi l'ultimo prezzo live reale, se non disponibile usa la chiusura di ieri
                if not df_live.empty:
                    ultimo_prezzo = float(df_live['Close'].iloc[-1])
                    prezzo_apertura = float(df_live['Open'].iloc[0])
                    # Calcola variazione percentuale odierna reale
                    variazione = ((ultimo_prezzo - prezzo_apertura) / prezzo_apertura) * 100
                else:
                    ultimo_prezzo = float(df['Close'].iloc[-1])
                    variazione = 0.0
                
                struttura_analisi[ticker] = {
                    "nome": nome,
                    "prezzo": ultimo_prezzo,
                    "variazione": variazione,
                    "sma20": f"{float(df['SMA20'].iloc[-1]):.2f}",
                    "sma50": f"{float(df['SMA50'].iloc[-1]):.2f}",
                    "rsi": f"{float(df['RSI14'].iloc[-1]):.1f}",
                    "segnale": elabora_rating_geopolitico(ticker, float(df['RSI14'].iloc[-1]))[0],
                    "motivazione": elabora_rating_geopolitico(ticker, float(df['RSI14'].iloc[-1]))[1]
                }
                print(f"✅ Dati estratti per {ticker}: {ultimo_prezzo}")
        except Exception as e:
            print(f"❌ Errore su {ticker}: {e}")
            
    output_finale = {
        "ultimo_aggiornamento_algoritmo": datetime.now().strftime("%H:%M:%S"),
        "analisi": struttura_analisi
    }
    
    with open("analisi.json", "w", encoding="utf-8") as f:
        json.dump(output_finale, f, indent=4, ensure_ascii=False)
    print("🎉 File 'analisi.json' salvato con successo!")

if __name__ == "__main__":
    main()
