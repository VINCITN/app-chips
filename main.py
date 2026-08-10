import pandas as pd
import yfinance as yf
import json
from datetime import datetime

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
    if ticker == "STM.MI":
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
            # Scarica lo storico per gli indicatori tecnici
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            
            # Recupera le informazioni rapide del ticker (contiene il prezzo corrente esatto)
            ticker_info = yf.Ticker(ticker).info
            
            if not df.empty and len(df) >= 50:
                df['SMA20'] = calcola_sma(df['Close'], window=20)
                df['SMA50'] = calcola_sma(df['Close'], window=50)
                df['RSI14'] = calcola_rsi(df['Close'], window=14)
                
                # Estrazione del prezzo sicuro ed esente da crash di sintassi
                ultimo_prezzo = ticker_info.get('regularMarketPrice') or ticker_info.get('currentPrice') or float(df['Close'].iloc[-1])
                variazione = ticker_info.get('regularMarketChangePercent') or 0.0
                
                ultimo_rsi = float(df['RSI14'].iloc[-1])
                segnale, motivazione = elabora_rating_geopolitico(ticker, ultimo_rsi)
                
                struttura_analysis = {
                    "nome": nome,
                    "prezzo": float(ultimo_prezzo),
                    "variazione": float(variazione),
                    "sma20": f"{float(df['SMA20'].iloc[-1]):.2f}",
                    "sma50": f"{float(df['SMA50'].iloc[-1]):.2f}",
                    "rsi": f"{ultimo_rsi:.1f}",
                    "segnale": segnale,
                    "motivazione": motivazione
                }
                # Rinomina la chiave rimuovendo i suffissi per l'HTML se necessario, ma teniamo la coerenza
                struttura_analisi[ticker] = struttura_analysis
                print(f"✅ Dati estratti correttamente per {ticker}: {ultimo_prezzo}")
                
        except Exception as e:
            print(f"❌ Errore saltato su {ticker}: {e}")
            
    output_finale = {
        "ultimo_aggiornamento_algoritmo": datetime.now().strftime("%H:%M:%S"),
        "analisi": struttura_analisi
    }
    
    with open("analisi.json", "w", encoding="utf-8") as f:
        json.dump(output_finale, f, indent=4, ensure_ascii=False)
    print("🎉 File 'analisi.json' salvato con successo!")

if __name__ == "__main__":
    main()
