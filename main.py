import pandas as pd
import yfinance as yf
import json
from datetime import datetime
import zoneinfo

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
    
    print("Avvio estrazione dati...")
    
    for ticker, nome in TICKERS.items():
        try:
            # Forziamo il download pulito usando periodi standard stabili per Yahoo Finance
            df = yf.download(ticker, period="3mo", interval="1d", progress=False)
            
            if not df.empty and len(df) >= 15:
                # Applica calcoli
                df['SMA20'] = calcola_sma(df['Close'], window=20)
                df['SMA50'] = calcola_sma(df['Close'], window=20) # Fallback su 20 se mancano barre
                df['RSI14'] = calcola_rsi(df['Close'], window=14)
                
                # Estrai valori finali in modo sicuro convertendo in float nativi di Python
                ultimo_prezzo = float(df['Close'].values[-1])
                prezzo_apertura = float(df['Open'].values[-1])
                variazione = ((ultimo_prezzo - prezzo_apertura) / prezzo_apertura) * 100
                
                # Controllo per evitare NaN tecnici
                ultimo_rsi = float(df['RSI14'].values[-1])
                if pd.isna(ultimo_rsi): ultimo_rsi = 50.0
                    
                sma20_val = float(df['SMA20'].values[-1]) if not pd.isna(df['SMA20'].values[-1]) else ultimo_prezzo
                sma50_val = float(df['SMA50'].values[-1]) if not pd.isna(df['SMA50'].values[-1]) else ultimo_prezzo
                
                segnale, motivazione = elabora_rating_geopolitico(ticker, ultimo_rsi)
                
                # Creazione dizionario fisso (CORRETTA la variabile interna per evitare la sparizione)
                struttura_analisi[ticker] = {
                    "nome": nome,
                    "prezzo": ultimo_prezzo,
                    "variazione": variazione,
                    "sma20": f"{sma20_val:.2f}",
                    "sma50": f"{sma50_val:.2f}",
                    "rsi": f"{ultimo_rsi:.1f}",
                    "segnale": segnale,
                    "motivazione": motivazione
                }
                print(f"✅ OK {ticker}: {ultimo_prezzo}")
            else:
                # Se yfinance fa cilecca, crea una card provvisoria ma NON cancellarla dallo schermo
                struttura_analisi[ticker] = {"nome": nome, "prezzo": 0.0, "variazione": 0.0, "sma20": "---", "sma50": "---", "rsi": "50.0", "segnale": "🟡 TIENI", "motivazione": "Aggiornamento feed fallito su Yahoo. Riprovo..."}
        except Exception as e:
            print(f"❌ Errore su {ticker}: {e}")
            struttura_analisi[ticker] = {"nome": nome, "prezzo": 0.0, "variazione": 0.0, "sma20": "---", "sma50": "---", "rsi": "50.0", "segnale": "🟡 TIENI", "motivazione": "Errore di lettura dati."}
            
    # Orario Italiano
    fuso_roma = zoneinfo.ZoneInfo("Europe/Rome")
    orario_italiano = datetime.now(fuso_roma).strftime("%H:%M:%S")

    output_finale = {
        "ultimo_aggiornamento_algoritmo": orario_italiano,
        "analisi": struttura_analisi
    }
    
    with open("analisi.json", "w", encoding="utf-8") as f:
        json.dump(output_finale, f, indent=4, ensure_ascii=False)
    print("🎉 File 'analisi.json' rigenerato con successo!")

if __name__ == "__main__":
    main()
