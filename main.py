import time
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
import requests

# --- CONFIGURAZIONE ASSET ---
TICKERS = {
    "STM.MI": "STMicroelectronics",
    "LDO.MI": "Leonardo S.p.A.",
    "NVDA": "NVIDIA Corp.",
    "TSM": "Taiwan Semiconductor",
    "ASML": "ASML Holding",
}

# --- FUNZIONI DI CALCOLO MATEMATICO ---
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

# --- GENERATORE DI SEGNALI GEOPOLITICI ---
def elabora_rating_geopolitico(ticker, rsi, macro_trend):
    trend_global_chip = "positivo" if macro_trend > 0 else "debole"
    
    if ticker == "STM.MI":
        if rsi < 35 and trend_global_chip == "positivo":
            return "🟢 COMPRA", "Le forti correzioni sul settore automotive offrono un punto d'ingresso. Il trend globale dell'AI (Nvidia/TSMC) fa da traino."
        elif rsi > 65:
            return "🔴 VENDI", "Titolo in ipercomprato tecnico. Le restrizioni USA sull'export e l'aumento dei costi pesano sui margini UE."
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
    analisi_output = {
        "ultimo_aggiornamento_algoritmo": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "analisi": {}
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    sessione = requests.Session()
    sessione.headers.update(headers)
    
    # 1. Raccoglie i dati storici degli ultimi 6 mesi
    dfs = {}
    variazioni = []
    
    for ticker in TICKERS.keys():
        try:
            df = yf.download(ticker, period="6mo", interval="1d", session=sessione, progress=False)
            if not df.empty:
                df.index = df.index.tz_localize(None)
                if isinstance(df.columns, pd.MultiIndex):
                    prezzi = df["Close"][ticker].values
                else:
                    prezzi = df["Close"].values
                
                df_pulito = pd.DataFrame(index=df.index)
                df_pulito["Close"] = pd.Series(prezzi, index=df.index).ffill().bfill().astype(float)
                dfs[ticker] = df_pulito
                
                # Calcola il trend odierno dei chip (NVDA, TSM, ASML)
                if len(df_pulito) > 1 and ticker in ["NVDA", "TSM", "ASML"]:
                    pct = (df_pulito["Close"].iloc[-1] - df_pulito["Close"].iloc[-2]) / df_pulito["Close"].iloc[-2]
                    variazioni.append(pct)
        except Exception as e:
            print(f"Errore analisi storica su {ticker}: {e}")

    trend_global = sum(variazioni) / len(variazioni) if variazioni else 0.0

    # 2. Calcola indicatori e genera i report geopolitici
    for ticker in ["STM.MI", "LDO.MI"]:
        if ticker in dfs:
            df = dfs[ticker]
            close_prices = df["Close"]
            
            sma20 = calcola_sma(close_prices, 20).iloc[-1]
            sma50 = calcola_sma(close_prices, 50).iloc[-1]
            rsi14 = calcola_rsi(close_prices, 14).iloc[-1]

            segnale, motivazione = elabora_rating_geopolitico(ticker, rsi14, trend_global)

            analisi_output["analisi"][ticker] = {
                "sma20": round(float(sma20), 2),
                "sma50": round(float(sma50), 2),
                "rsi": round(float(rsi14), 2),
                "segnale": segnale,
                "motivazione": motivazione
            }
            
    # 3. Salva l'analisi in analisi.json
    with open("analisi.json", "w") as f:
        json.dump(analisi_output, f, indent=4)
    print("Analisi geopolitica salvata con successo in analisi.json!")

if __name__ == "__main__":
    scarica_e_analizza()
