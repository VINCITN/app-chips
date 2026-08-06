import requests_cache
# Mantiene i dati in memoria per 2 minuti (120 secondi)
yf.set_proxy_session(requests_cache.CachedSession('yfinance.cache', expire_after=120))
from datetime import datetime
import streamlit as st
import yfinance as yf
st.set_page_config(page_title="Crypto & Chip Dashboard", layout="wide")
st.title("📊 Dashboard Algoritmica Semiconduttori & Geopolitica")
st.write("L'applicazione incrocia i dati di mercato con i produttori mondiali di chip e gli indici geopolitici.")

# Bottone di aggiornamento (Streamlit ricarica la pagina in automatico al click)
if st.button("🔄 Aggiorna Quotazioni Ora (In Tempo Reale)"):
    st.toast("Download dati di mercato in corso...")

# Configurazione Tickers
TITOLI_MILANO = {"STM.MI": "STMicroelectronics", "LDO.MI": "Leonardo S.p.A."}
TICKERS_CHIPS = {"NVDA": "NVIDIA (USA)", "TSM": "TSMC (Asia)", "ASML": "ASML (Europa)"}
TICKERS_GEOPOLITICA = {"^VIX": "Indice Incertezza (VIX)", "ITA": "Fondo Difesa Globale (iShares)"}

# --- 1. COMPARTO CHIP INTERNAZIONALE ---
st.subheader("🌐 Comparto Chip Internazionale")
cols_chips = st.columns(3)
somma_var_chips, conteggio_chips = 0, 0

for i, (ticker, nome) in enumerate(TICKERS_CHIPS.items()):
    try:
        t = yf.Ticker(ticker)
        # Periodo '2d' a intervallo giornaliero evita i blocchi dei dati al minuto
        df = t.history(period="2d")
        if len(df) >= 1:
            prezzo_attuale = df["Close"].iloc[-1]
            # Gestione della variazione percentuale
            chiusura_ieri = t.info.get("previousClose") if t.info else None
            if not chiusura_ieri and len(df) > 1:
                chiusura_ieri = df["Close"].iloc[-2]
            
            var = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100 if chiusura_ieri else 0.0
            
            somma_var_chips += var
            conteggio_chips += 1
            cols_chips[i].metric(label=nome, value=f"{prezzo_attuale:.2f} USD", delta=f"{var:+.2f}%")
        else:
            cols_chips[i].warning(f"Dati non disponibili per {nome}")
    except Exception as e:
        cols_chips[i].error(f"Errore {nome}")

momentum_chips_globale = somma_var_chips / conteggio_chips if conteggio_chips > 0 else 0

# --- 2. SCENARIO GEOPOLITICO INTERNAZIONALE ---
st.subheader("⚔️ Scenario Geopolitico Internazionale")
cols_geo = st.columns(2)
var_vix, var_difesa = 0.0, 0.0

for i, (ticker, nome) in enumerate(TICKERS_GEOPOLITICA.items()):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="2d")
        if len(df) >= 1:
            prezzo_attuale = df["Close"].iloc[-1]
            chiusura_ieri = t.info.get("previousClose") if t.info else None
            if not chiusura_ieri and len(df) > 1:
                chiusura_ieri = df["Close"].iloc[-2]
                
            var = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100 if chiusura_ieri else 0.0
            
            cols_geo[i].metric(label=nome, value=f"{prezzo_attuale:.2f}", delta=f"{var:+.2f}%")
            if ticker == "^VIX": var_vix = var
            elif ticker == "ITA": var_difesa = var
        else:
            cols_geo[i].warning(f"Dati non disponibili per {nome}")
    except Exception as e:
        cols_geo[i].error(f"Errore {nome}")

# --- 3. SEGNALI OPERATIVI PIAZZA AFFARI ---
st.subheader("🇮🇹 Segnali Operativi Piazza Affari (Valuta: EURO)")
cols_milano = st.columns(2)

for i, (ticker, nome) in enumerate(TITOLI_MILANO.items()):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="2d")
        if len(df) >= 1:
            prezzo_in_euro = df["Close"].iloc[-1]
            apertura_oggi = df["Open"].iloc[-1]
            var_giornaliera_milano = ((prezzo_in_euro - apertura_oggi) / apertura_oggi) * 100

            # Algoritmo di Score Geopolitico
            if "STM" in ticker:
                score = (var_giornaliera_milano * 0.5) + (momentum_chips_globale * 0.4) - (var_vix * 0.1)
                soglia_buy, soglia_sell = 0.4, -0.4
            else:
                score = (var_giornaliera_milano * 0.5) + (var_difesa * 0.3) + (var_vix * 0.2)
                soglia_buy, soglia_sell = 0.3, -0.3

            # Correzione logica colori visivi (Verde per comprare, Rosso per vendere)
            if score > soglia_buy: 
                verdetto, colore = "🟢 COMPRARE (BUY)", "success"
            elif score < soglia_sell: 
                verdetto, colore = "🔴 VENDERE (SELL)", "error"
            else: 
                verdetto, colore = "🟡 TENERE (HOLD)", "warning"

            with cols_milano[i]:
                st.metric(label=f"{nome} ({ticker})", value=f"{prezzo_in_euro:.2f} €", delta=f"{var_giornaliera_milano:+.2f}%")
                st.markdown(f"**Score Algoritmico:** `{score:+.2f}`")
                if colore == "success": st.success(f"STRATEGIA: {verdetto}")
                elif colore == "error": st.error(f"STRATEGIA: {verdetto}")
                else: st.warning(f"STRATEGIA: {verdetto}")
        else:
            cols_milano[i].warning(f"Dati non disponibili per {nome}")
    except Exception as e:
        cols_milano[i].error(f"Errore {nome}")

st.divider()
st.caption(f"Ultimo controllo eseguito il: {datetime.now().strftime('%d/%m/%Y alle %H:%M:%S')}")
