import time
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
import requests

TICKERS = {
    "STM": "STMicroelectronics",
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
    avg_loss = loss.rolling(window=window).mean()
    avg_loss = avg_loss.replace(0, 0.00001)
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
    return "⚖️ NEUTRALE", "Nessuna anomalia macroeconomica rilevata."

def scarica_e_analizza():
    output = {
        "ultimo_aggiornamento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "titoli": {}
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    sessione = requests.Session()
    sessione.headers.update(headers)
    
    dfs = {}
    variazioni = []
    
    # Scarica dati storici per indicatori
    for ticker in TICKERS.keys():
        try:
            df = yf.download(ticker, period="6mo", interval="1d", session=sessione, progress=False)
            if not df.empty:
                df.index = df.index.tz_localize(None)
                prezzi = df["Close"][ticker].values if isinstance(df.columns, pd.MultiIndex) else df["Close"].values
                df_pulito = pd.DataFrame(index=df.index)
                df_pulito["Close"] = pd.Series(prezzi, index=df.index).ffill().bfill().astype(float)
                dfs[ticker] = df_pulito
                if len(df_pulito) > 1 and ticker in ["NVDA", "TSM", "ASML"]:
                    pct = (df_pulito["Close"].iloc[-1] - df_pulito["Close"].iloc[-2]) / df_pulito["Close"].iloc[-2]
                    variazioni.append(pct)
        except Exception as e:
            print(f"Errore storico su {ticker}: {e}")

    trend_global = sum(variazioni) / len(variazioni) if variazioni else 0.0

    # Scarica prezzi spot in tempo reale dell'ultimo minuto
    for ticker, nome in TICKERS.items():
        try:
            ticker_data = yf.Ticker(ticker, session=sessione)
            info_veloce = ticker_data.fast_info
            prezzo_live = info_veloce['lastPrice']
            
            # Calcola la variazione percentuale odierna
            prezzo_chiusura_prev = dfs[ticker]["Close"].iloc[-2] if ticker in dfs and len(dfs[ticker]) > 1 else prezzo_live
            var_pct = ((prezzo_live - prezzo_chiusura_prev) / prezzo_chiusura_prev) * 100
        except Exception:
            # Fallback se fast_info fallisce
            prezzo_live = dfs[ticker]["Close"].iloc[-1] if ticker in dfs else 0.0
            var_pct = 0.0

        # Calcola metriche algoritmiche
        sma20, sma50, rsi14 = "-", "-", "-"
        segnale, motivazione = "⚖️ NEUTRALE", "Inizializzazione analisi macro..."
        
        if ticker in dfs:
            df = dfs[ticker]
            sma20 = round(float(calcola_sma(df["Close"], 20).iloc[-1]), 2)
            sma50 = round(float(calcola_sma(df["Close"], 50).iloc[-1]), 2)
            rsi14 = round(float(calcola_rsi(df["Close"], 14).iloc[-1]), 2)
            if ticker in ["STM", "LDO.MI"]:
                segnale, motivazione = elabora_rating_geopolitico(ticker, rsi14, trend_global)

        output["titoli"][ticker] = {
            "nome": nome,
            "prezzo": round(prezzo_live, 2) if ticker != "BTC-USD" else round(prezzo_live, 0),
            "variazione": round(var_pct, 2),
            "sma20": sma20,
            "sma50": sma50,
            "rsi": rsi14,
            "segnale": segnale,
            "motivazione": motivazione
        }
            
    with open("analisi.json", "w") as f:
        json.dump(output, f, indent=4)
    print("Dati strutturati salvati in analisi.json!")

if __name__ == "__main__":
    scarica_e_analizza()
