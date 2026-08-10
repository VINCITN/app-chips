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
    print("Avvio estrazione flussi reali sul server...")
    
    for ticker, nome in TICKERS.items():
        try:
            # 1. Scarica lo storico per l'analisi tecnica
            ticker_dl = "STM" if ticker == "STM.MI" else ticker
            df = yf.download(ticker_dl, period="60d", interval="1d", progress=False)
            
            # 2. Estrai il prezzo e la variazione in tempo reale senza usare l'HTML del browser
            t = yf.Ticker(ticker)
            prezzo_reale = float(t.fast_info.get('lastPrice', 0.0))
            
            # Calcola la variazione percentuale reale basata sulla chiusura precedente
            chiusura_precedente = float(t.fast_info.get('previousClose', prezzo_reale))
            if chiusura_precedente > 0:
                variazione_reale = ((prezzo_reale - chiusura_precedente) / chiusura_precedente) * 100
            else:
                variazione_reale = 0.0

            if not df.empty and len(df) >= 15:
                df['SMA20'] = calcola_sma(df['Close'], window=20)
                df['SMA50'] = calcola_sma(df['Close'], window=20)
                df['RSI14'] = calcola_rsi(df['Close'], window=14)
                
                ultimo_rsi = float(df['RSI14'].values[-1])
                if pd.isna(ultimo_rsi): ultimo_rsi = 50.0
                
                sma20_val = float(df['SMA20'].values[-1]) if not pd.isna(df['SMA20'].values[-1]) else prezzo_reale
                sma50_val = float(df['SMA50'].values[-1]) if not pd.isna(df['SMA50'].values[-1]) else prezzo_reale
                
                # Se per STM avevamo usato il ticker USA per la SMA, riallineiamo il prezzo proporzionalmente
                if ticker == "STM.MI" and sma20_val > 50:
                    sma20_val = sma20_val * (prezzo_reale / float(df['Close'].values[-1]))
                    sma50_val = sma50_val * (prezzo_reale / float(df['Close'].values[-1]))

                segnale, motivazione = elabora_rating_geopolitico(ticker, ultimo_rsi)
                
                struttura_analisi[ticker] = {
                    "nome": nome,
                    "prezzo": prezzo_reale,
                    "variazione": variazione_reale,
                    "sma20": f"{sma20_val:.2f}",
                    "sma50": f"{sma50_val:.2f}",
                    "rsi": f"{ultimo_rsi:.1f}",
                    "segnale": segnale,
                    "motivazione": motivazione
                }
                print(f"✅ Sincronizzato {ticker}: {prezzo_reale:.2f}")
        except Exception as e:
            print(f"❌ Errore su {ticker}: {e}")
            
    fuso_roma = zoneinfo.ZoneInfo("Europe/Rome")
    orario_italiano = datetime.now(fuso_roma).strftime("%H:%M:%S")

    output_finale = {
        "ultimo_aggiornamento_algoritmo": orario_italiano,
        "analisi": struttura_analisi
    }
    
    with open("analisi.json", "w", encoding="utf-8") as f:
        json.dump(output_finale, f, indent=4, ensure_ascii=False)
    print("🎉 Database centralizzato salvato con successo!")

if __name__ == "__main__":
    main()
