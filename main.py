import pandas as pd
import yfinance as yf
import json
from datetime import datetime
import zoneinfo

# Usiamo STM americano per evitare il blocco del server sul mercato di Milano
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
        elif rsi > 65: return "🔴 VENDI", "Titolo in ipercomprato tecnico. Restrizioni export USA pesano sui margins."
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
    
    # 1. Recupera il tasso di cambio reale EUR/USD per la conversione di STM
    tasso_cambio = 1.10 # Valore di fallback sicuro
    try:
        fx = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        if not fx.empty:
            tasso_cambio = float(fx['Close'].values[-1])
    except:
        pass

    print(f"Avvio estrazione flussi (Tasso EUR/USD: {tasso_cambio})...")
    
    for ticker, nome in TICKERS.items():
        try:
            # Per evitare il blocco di Milano, interroghiamo STM sul mercato USA
            ticker_download = "STM" if ticker == "STM.MI" else ticker
            
            df = yf.download(ticker_download, period="3mo", interval="1d", progress=False)
            
            if not df.empty and len(df) >= 15:
                df['SMA20'] = calcola_sma(df['Close'], window=20)
                df['SMA50'] = calcola_sma(df['Close'], window=50) if len(df) >= 50 else calcola_sma(df['Close'], window=20)
                df['RSI14'] = calcola_rsi(df['Close'], window=14)
                
                ultimo_prezzo = float(df['Close'].values[-1])
                prezzo_apertura = float(df['Open'].values[-1])
                variazione = ((ultimo_prezzo - prezzo_apertura) / prezzo_apertura) * 100
                
                # SE È IL TICKER DI MILANO, CONVERTI IL PREZZO DA DOLLARI A EURO
                if ticker == "STM.MI":
                    ultimo_prezzo = ultimo_prezzo / tasso_cambio
                    
                ultimo_rsi = float(df['RSI14'].values[-1])
                if pd.isna(ultimo_rsi): ultimo_rsi = 50.0
                    
                sma20_val = float(df['SMA20'].values[-1]) if not pd.isna(df['SMA20'].values[-1]) else ultimo_prezzo
                sma50_val = float(df['SMA50'].values[-1]) if not pd.isna(df['SMA50'].values[-1]) else ultimo_prezzo
                
                if ticker == "STM.MI":
                    sma20_val = sma20_val / tasso_cambio
                    sma50_val = sma50_val / tasso_cambio
                
                segnale, motivazione = elabora_rating_geopolitico(ticker, ultimo_rsi)
                
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
                print(f"✅ Dati pronti per {ticker}: {ultimo_prezzo:.2f}")
        except Exception as e:
            print(f"❌ Errore su {ticker}: {e}")
            
    # Orario Italiano
    fuso_roma = zoneinfo.ZoneInfo("Europe/Rome")
    orario_italiano = datetime.now(fuso_roma).strftime("%H:%M:%S")

    output_finale = {
        "ultimo_aggiornamento_algoritmo": orario_italiano,
        "analisi": struttura_analisi
    }
    
    with open("analisi.json", "w", encoding="utf-8") as f:
        json.dump(output_finale, f, indent=4, ensure_ascii=False)
    print("🎉 Architettura dati completata con successo!")

if __name__ == "__main__":
    main()
