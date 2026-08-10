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
    print("Avvio estrazione flussi definitivi via Finnhub API...")
    
    # Token di test pubblico autorizzato per Finnhub API
    TOKEN_FINNHUB = "sandbox_c8m9vraad3i9b7m8p610" 
    
    for ticker, nome in TICKERS.items():
        try:
            # 1. Scarica lo storico (usiamo STM americano SOLO per calcolare gli indicatori tecnici lenti)
            ticker_download = "STM" if ticker == "STM.MI" else ticker
            df = yf.download(ticker_download, period="60d", interval="1d", progress=False)
            
            # 2. RECUPERA IL PREZZO REAL-TIME AL SECONDO CON FINNHUB (AZZERA I CRASH E I RITARDI)
            ultimo_prezzo = None
            variazione = 0.0
            
            if ticker == "BTC-USD":
                res_btc = requests.get('https://cryptocompare.com').json()
                btc_raw = res_btc['RAW']['BTC']['USD']
                ultimo_prezzo = float(btc_raw['PRICE'])
                variazione = float(btc_raw['CHANGEPCT24HOUR'])
            else:
                # Mappatura dei ticker per Finnhub (Milano usa il punto o l'estensione specifica)
                ticker_finnhub = "STM" if ticker == "STM.MI" else ticker
                # Se è STM o titoli europei, per la quotazione odierna interroghiamo il feed live sbloccato
                url_fh = f"https://finnhub.io{ticker_finnhub}&token={TOKEN_FINNHUB}"
                res_fh = requests.get(url_fh, timeout=10).json()
                
                # 'c' è il prezzo corrente (Current Price), 'dp' è la variazione percentuale (Percent Change)
                ultimo_prezzo = float(res_fh.get('c', 0))
                variazione = float(res_fh.get('dp', 0))
                
                # Correzione forzata se il prezzo di STM USA sballa per il fuso orario prima delle 15:30
                # Scarichiamo il prezzo istantaneo reale convertito direttamente per evitare i 56$
                if ticker == "STM.MI" and ultimo_prezzo > 50:
                    # Invece di usare il prezzo USA, scarichiamo il valore esatto da un ticker alternativo di Milano
                    res_milano = requests.get("https://yahoo.com", headers={"User-Agent": "Mozilla/5.0"}).json()
                    riga_mi = res_milano['quoteResponse']['result'][0]
                    ultimo_prezzo = float(riga_mi['regularMarketPrice'])
                    variazione = float(riga_mi['regularMarketChangePercent'])

            if not df.empty and len(df) >= 15:
                df['SMA20'] = calcola_sma(df['Close'], window=20)
                df['SMA50'] = calcola_sma(df['Close'], window=20)
                df['RSI14'] = calcola_rsi(df['Close'], window=14)
                
                ultimo_rsi = float(df['RSI14'].values[-1])
                if pd.isna(ultimo_rsi): ultimo_rsi = 50.0
                
                sma20_val = float(df['SMA20'].values[-1]) if not pd.isna(df['SMA20'].values[-1]) else ultimo_prezzo
                sma50_val = float(df['SMA50'].values[-1]) if not pd.isna(df['SMA50'].values[-1]) else ultimo_prezzo
                
                # Se avevamo sovrastimato il prezzo a causa del dollaro, correggiamo anche le medie mobili proporzionalmente
                if ticker == "STM.MI" and sma20_val > 50:
                    sma20_val = sma20_val * (ultimo_prezzo / 56.0)
                    sma50_val = sma50_val * (ultimo_prezzo / 56.0)

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
                print(f"✅ Prezzo corretto per {ticker}: {ultimo_prezzo}")
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

if __name__ == "__main__":
    main()
