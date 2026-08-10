import pandas as pd
import yfinance as yf
import json
import requests
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
    print("Avvio estrazione flussi stabili ad alta tolleranza...")
    
    for ticker, nome in TICKERS.items():
        try:
            # Scarica lo storico (usiamo ticker americani stabili per gli indicatori tecnici lenti per evitare blocchi)
            ticker_download = "STM" if ticker == "STM.MI" else ("LDO.MI" if ticker == "LDO.MI" else ticker)
            df = yf.download(ticker_download, period="60d", interval="1d", progress=False)
            
            ultimo_prezzo = 0.0
            variazione = 0.0
            
            # RECUPERO PREZZI LIVE BLINDATO DA SORGENTI SBLOCCATE (STOOQ E CRYPTOCOMPARE)
            if ticker == "BTC-USD":
                res_btc = requests.get('https://cryptocompare.com').json()
                btc_raw = res_btc['RAW']['BTC']['USD']
                ultimo_prezzo = float(btc_raw['PRICE'])
                variazione = float(btc_raw['CHANGEPCT24HOUR'])
            else:
                # Mappatura dei codici per l'API Stooq aperta (stm.it, ldo.it, nvda.us, ecc.)
                codice_stooq = "ldo.it" if ticker == "LDO.MI" else ("stm.it" if ticker == "STM.MI" else f"{ticker.lower()}.us")
                url_stooq = f"https://stooq.com{codice_stooq}"
                res_sq = requests.get(url_stooq, timeout=10).json()
                if 'aq' in res_sq:
                    riga = res_sq['aq']
                    ultimo_prezzo = float(riga.get('l1', 0.0))
                    variazione = float(riga.get('c1', 0.0))
            
            # Se l'API Stooq fallisce, usiamo l'ultimo valore disponibile da Yahoo
            if ultimo_prezzo == 0.0 and not df.empty:
                ultimo_prezzo = float(df['Close'].iloc[-1])

            if not df.empty and len(df) >= 15:
                df['SMA20'] = calcola_sma(df['Close'], window=20)
                df['SMA50'] = calcola_sma(df['Close'], window=20)
                df['RSI14'] = calcola_rsi(df['Close'], window=14)
                
                ultimo_rsi = float(df['RSI14'].iloc[-1])
                if pd.isna(ultimo_rsi): ultimo_rsi = 50.0
                    
                sma20_val = float(df['SMA20'].iloc[-1]) if not pd.isna(df['SMA20'].iloc[-1]) else ultimo_prezzo
                sma50_val = float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else ultimo_prezzo
                
                segnale, motivazione = elabora_rating_geopolitico(ticker, ultimo_rsi)
                
                struttura_analisi[ticker] = {
                    "nome": nome,
                    "prezzo": float(ultimo_prezzo),
                    "variazione": float(variazione),
                    "sma20": f"{sma20_val:.2f}",
                    "sma50": f"{sma50_val:.2f}",
                    "rsi": f"{ultimo_rsi:.1f}",
                    "segnale": segnale,
                    "motivazione": motivazione
                }
                print(f"✅ Compilato {ticker}: {ultimo_prezzo:.2f}")
        except Exception as e:
            print(f"❌ Errore saltato su {ticker}: {e}")
            
    fuso_roma = zoneinfo.ZoneInfo("Europe/Rome")
    orario_italiano = datetime.now(fuso_roma).strftime("%H:%M:%S")

    output_finale = {
        "ultimo_aggiornamento_algoritmo": orario_italiano,
        "analisi": struttura_analisi
    }
    
    with open("analisi.json", "w", encoding="utf-8") as f:
        json.dump(output_finale, f, indent=4, ensure_ascii=False)
    print("🎉 File 'analisi.json' salvato con successo!")

if __name__ == "__main__":
    main()
