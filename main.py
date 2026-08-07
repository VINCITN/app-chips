import time
import json
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import requests

# --- CONFIGURAZIONE ---
TICKERS = {
    "STM.MI": "STMicroelectronics",
    "LDO.MI": "Leonardo S.p.A.",
    "NVDA": "NVIDIA Corp.",
    "TSM": "Taiwan Semiconductor",
    "ASML": "ASML Holding",
    "BTC-USD": "Bitcoin",
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
    dati_output = {
        "ultimo_aggiornamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "titoli": {}
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    sessione = requests.Session()
    sessione.headers.update(headers)
    
    # Calcolo del trend globale dei chip basato su NVDA, TSM, ASML
    trend_global = 0.0
    variazioni = []
    
    # Primo ciclo per raccogliere dati finanziari stabili
    dfs = {}
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
                
                # Calcola variazione percentuale odierna per il trend macro
                if len(df_pulito) > 1:
                    pct = (df_pulito["Close"].iloc[-1] - df_pulito["Close"].iloc[-2]) / df_pulito["Close"].iloc[-2]
                    if ticker in ["NVDA", "TSM", "ASML"]:
                        variazioni.append(pct)
        except Exception as e:
            print(f"Errore su {ticker}: {e}")

    if variazioni:
        trend_global = sum(variazioni) / len(variazioni)

    # Secondo ciclo per calcolare indicatori e segnali geopolitici
    for ticker, nome in TICKERS.items():
        if ticker in dfs:
            df = dfs[ticker]
            close_prices = df["Close"]
            
            # Calcolo indicatori algoritmici
            sma20 = calcola_sma(close_prices, 20).iloc[-1]
            sma50 = calcola_sma(close_prices, 50).iloc[-1]
            rsi14 = calcola_rsi(close_prices, 14).iloc[-1]
            prezzo_attuale = float(close_prices.iloc[-1])
            prezzo_precedente = float(close_prices.iloc[-2]) if len(close_prices) > 1 else prezzo_attuale
            variazione_pct = ((prezzo_attuale - prezzo_precedente) / prezzo_precedente) * 100

            # Genera segnale geopolitico solo per STM e Leonardo
            segnale, motivazione = elabora_rating_geopolitico(ticker, rsi14, trend_global)

            dati_output["titoli"][ticker] = {
                "nome": nome,
                "prezzo": round(prezzo_attuale, 2) if ticker != "BTC-USD" else round(prezzo_attuale, 0),
                "variazione": round(variazione_pct, 2),
                "sma20": round(float(sma20), 2),
                "sma50": round(float(sma50), 2),
                "rsi": round(float(rsi14), 2),
                "segnale": segnale,
                "motivazione": motivazione
            }
            
    # Salva i dati strutturati in dati.json
    with open("dati.json", "w") as f:
        json.dump(dati_output, f, indent=4)
    print("Dati aggiornati con successo in dati.json")

if __name__ == "__main__":
    scarica_e_analizza()
