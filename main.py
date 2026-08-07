import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import json
from datetime import datetime
import zoneinfo # <--- Aggiungi questa libreria nativa

# Configurazione della Dashboard visiva
st.set_page_config(page_title="Monitor Chip 1-Minuto", layout="wide")
st.title("📊 Monitor Flussi Chip & Geopolitica (Aggiornamento 1 Minuto)")

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
    avg_loss = loss.rolling(window=window).mean().replace(0, 0.00001)
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

# --- PROTEZIONE BAN IP: Scarica lo storico pesante solo una volta all'ora ---
@st.cache_data(ttl=3600)
def scarica_dati_storici():
    headers = {"User-Agent": "Mozilla/5.0"}
    sessione = requests.Session()
    sessione.headers.update(headers)
    dfs = {}
    variazioni = []
    
    for ticker in TICKERS.keys():
        try:
            df = yf.download(ticker, period="6mo", interval="1d", session=sessione, progress=False)
            if not df.empty:
                # Correzione formattazione colonne MultiIndex di yfinance
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df.index = df.index.tz_localize(None)
                
                df_pulito = pd.DataFrame(index=df.index)
                df_pulito["Close"] = df["Close"].ffill().bfill().astype(float)
                dfs[ticker] = df_pulito
                
                if len(df_pulito) > 1 and ticker in ["NVDA", "TSM", "ASML"]:
                    pct = (df_pulito["Close"].iloc[-1] - df_pulito["Close"].iloc[-2]) / df_pulito["Close"].iloc[-2]
                    variazioni.append(pct)
        except Exception:
            pass
    trend_global = sum(variazioni) / len(variazioni) if variazioni else 0.0
    return dfs, trend_global

# Forza la pagina web ad aggiornarsi da sola ogni 60000 millisecondi (1 minuto)
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60000, key="datarefresh")

# Recupera lo storico memorizzato temporaneamente
dfs, trend_global = scarica_dati_storici()

tabella_dati = []

# Configura il calcolo sull'orario italiano
fuso_orario_italia = zoneinfo.ZoneInfo("Europe/Rome")
output_json = {
    "ultimo_aggiornamento": datetime.now(fuso_orario_italia).strftime("%d/%m/%Y %H:%M:%S"),
    "titoli": {}
}

# --- AGGIORNAMENTO PREZZO LIVE (Ogni minuto) ---
headers = {"User-Agent": "Mozilla/5.0"}
sessione_live = requests.Session()
sessione_live.headers.update(headers)

for ticker, nome in TICKERS.items():
    try:
        ticker_data = yf.Ticker(ticker, session=sessione_live)
        prezzo_live = float(ticker_data.fast_info['lastPrice'])
        prezzo_chiusura_prev = dfs[ticker]["Close"].iloc[-2] if ticker in dfs and len(dfs[ticker]) > 1 else prezzo_live
        var_pct = ((prezzo_live - prezzo_chiusura_prev) / prezzo_chiusura_prev) * 100
    except Exception:
        # Paracadute se la richiesta live fallisce momentaneamente
        prezzo_live = float(dfs[ticker]["Close"].iloc[-1]) if ticker in dfs else 0.0
        var_pct = 0.0

    sma20, sma50, rsi14 = "-", "-", "-"
    segnale, motivazione = "⚖️ NEUTRALE", "Analisi di mercato..."
    
    if ticker in dfs and not dfs[ticker].empty:
        df_indici = dfs[ticker]
        try:
            sma20 = round(float(calcola_sma(df_indici["Close"], 20).iloc[-1]), 2)
            sma50 = round(float(calcola_sma(df_indici["Close"], 50).iloc[-1]), 2)
            rsi14 = round(float(calcola_rsi(df_indici["Close"], 14).iloc[-1]), 2)
            if ticker in ["STM", "LDO.MI"]:
                segnale, motivazione = elabora_rating_geopolitico(ticker, rsi14, trend_global)
        except Exception:
            pass

    # Genera riga per la tabella a schermo
    tabella_dati.append({
        "Ticker": ticker,
        "Nome": nome,
        "Prezzo Live": round(prezzo_live, 2) if ticker != "BTC-USD" else round(prezzo_live, 0),
        "Variazione %": f"{var_pct:+.2f}%",
        "SMA 20": sma20,
        "SMA 50": sma50,
        "RSI (14)": rsi14,
        "Segnale Geopolitico": segnale,
        "Scenario / Valutazione": motivazione
    })

    # Genera dati per il file JSON locale
    output_json["titoli"][ticker] = {
        "nome": nome, "prezzo": prezzo_live, "variazione": var_pct,
        "sma20": sma20, "sma50": sma50, "rsi": rsi14,
        "segnale": segnale, "motivazione": motivazione
    }

# Salva il file JSON sul server di Streamlit ogni minuto
with open("analisi.json", "w") as f:
    json.dump(output_json, f, indent=4)

# Mostra i risultati visivi
st.write(f"⏱️ **Ultimo controllo effettuato il:** {output_json['ultimo_aggiornamento']}")
df_visivo = pd.DataFrame(tabella_dati)
st.dataframe(df_visivo, use_container_width=True, hide_index=True)
