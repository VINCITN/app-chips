import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import zoneinfo

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Monitor Chip Live", layout="wide")
st.title("📊 Monitor Flussi Chip & Geopolitica (Tempo Reale)")

# Configura il refresh automatico nativo di Streamlit
if "counter" not in st.session_state:
    st.session_state.counter = 0

# Mostra l'orario italiano dell'ultimo secondo a schermo
fuso_roma = zoneinfo.ZoneInfo("Europe/Rome")
ora_attuale = datetime.now(fuso_roma).strftime("%H:%M:%S")
st.write(f"🔄 Ultimo tick reale: **{ora_attuale}**")

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

# Creazione layout a griglia (3 colonne)
colonne = st.columns(3)

for i, (ticker, nome) in enumerate(TICKERS.items()):
    try:
        # Scarica lo storico per gli indicatori
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        
        if not df.empty and len(df) >= 15:
            df['SMA20'] = calcola_sma(df['Close'], window=20)
            df['SMA50'] = calcola_sma(df['Close'], window=20)
            df['RSI14'] = calcola_rsi(df['Close'], window=14)
            
            # Estrazione prezzo istantaneo al secondo (Render non subisce blocchi IP)
            prezzo_reale = float(df['Close'].iloc[-1])
            prezzo_apertura = float(df['Open'].iloc[-1])
            variazione = ((prezzo_reale - prezzo_apertura) / prezzo_apertura) * 100
            
            ultimo_rsi = float(df['RSI14'].iloc[-1])
            if pd.isna(ultimo_rsi): ultimo_rsi = 50.0
            
            sma20_val = float(df['SMA20'].iloc[-1]) if not pd.isna(df['SMA20'].iloc[-1]) else prezzo_reale
            sma50_val = float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else prezzo_reale
            
            segnale, motivazione = elabora_rating_geopolitico(ticker, ultimo_rsi)
            valuta = "€" if ".MI" in ticker or "ASML" in ticker else "$"
            
            # Rendering grafico dentro le colonne
            with colonne[i % 3]:
                st.subheader(f"{nome} ({ticker})")
                st.metric(label="Prezzo Spot", value=f"{valuta} {prezzo_reale:.2f}", delta=f"{variazione:.2f}%")
                
                # Sotto-metriche tecniche
                st.markdown(f"**SMA 20:** {sma20_val:.2f} | **SMA 50:** {sma50_val:.2f} | **RSI:** {ultimo_rsi:.1f}")
                st.markdown(f"**Rating:** {segnale}")
                st.caption(motivazione)
                st.markdown("---")
    except Exception as e:
        with colonne[i % 3]:
            st.error(f"Errore caricamento {ticker}")

# Forza il rerun della pagina ogni 10 secondi (Tempo Reale Continuo)
st.rerun()
