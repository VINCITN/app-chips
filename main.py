from datetime import datetime
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Crypto & Chip Dashboard", layout="wide")
st.title("📊 Dashboard Algoritmica Semiconduttori & Geopolitica")
st.write("L'applicazione incrocia i dati di Milano con i produttori mondiali di chip e gli indici geopolitici.")

if st.button("🔄 Aggiorna Quotazioni Ora (In Tempo Reale)"):
    st.toast("Download dati di mercato in corso...")

TITOLI_MILANO = {"STM.MI": "STMicroelectronics", "LDO.MI": "Leonardo S.p.A."}
TICKERS_CHIPS = {"NVDA": "NVIDIA (USA)", "TSM": "TSMC (Asia)", "ASML": "ASML (Europa)"}
TICKERS_GEOPOLITICA = {"^VIX": "Indice Incertezza (VIX)", "ITA": "Fondo Difesa Globale (iShares)"}

st.subheader("🌐 Comparto Chip Internazionale")
cols_chips = st.columns(3)
somma_var_chips, conteggio_chips = 0, 0

for i, (ticker, nome) in enumerate(TICKERS_CHIPS.items()):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1d", interval="1m")
        if not df.empty:
            chiusura_ieri = t.info.get("previousClose", df["Close"].iloc[-1])
            var = ((df["Close"].iloc[-1] - chiusura_ieri) / chiusura_ieri) * 100
            somma_var_chips += var
            conteggio_chips += 1
            cols_chips[i].metric(label=nome, value=f"{df['Close'].iloc[-1]:.2f} USD", delta=f"{var:+.2f}%")
    except Exception:
        cols_chips[i].error(f"Errore {nome}")

momentum_chips_globale = somma_var_chips / conteggio_chips if conteggio_chips > 0 else 0

st.subheader("⚔️ Scenario Geopolitico Internazionale")
cols_geo = st.columns(2)
var_vix, var_difesa = 0.0, 0.0

for i, (ticker, nome) in enumerate(TICKERS_GEOPOLITICA.items()):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1d", interval="1m")
        if not df.empty:
            chiusura_ieri = t.info.get("previousClose", df["Close"].iloc[-1])
            var = ((df["Close"].iloc[-1] - chiusura_ieri) / chiusura_ieri) * 100
            cols_geo[i].metric(label=nome, value=f"{df['Close'].iloc[-1]:.2f}", delta=f"{var:+.2f}%")
            if ticker == "^VIX": var_vix = var
            elif ticker == "ITA": var_difesa = var
    except Exception:
        cols_geo[i].error(f"Errore {nome}")

st.subheader("🇮🇹 Segnali Operativi Piazza Affari (Valuta: EURO)")
cols_milano = st.columns(2)

for i, (ticker, nome) in enumerate(TITOLI_MILANO.items()):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1d", interval="1m")
        if not df.empty:
            prezzo_in_euro = df["Close"].iloc[-1]
            df_giorno = t.history(period="1d")
            var_giornaliera_milano = ((prezzo_in_euro - df_giorno["Open"].iloc[-1]) / df_giorno["Open"].iloc[-1]) * 100

            if "STM" in ticker:
                score = (var_giornaliera_milano * 0.5) + (momentum_chips_globale * 0.4) - (var_vix * 0.1)
                soglia_buy, soglia_sell = 0.4, -0.4
            else:
                score = (var_giornaliera_milano * 0.5) + (var_difesa * 0.3) + (var_vix * 0.2)
                soglia_buy, soglia_sell = 0.3, -0.3

            if score > soglia_buy: verdetto, colore = "🔴 COMPRARE (BUY)", "error"
            elif score < soglia_sell: verdetto, colore = "🟢 VENDERE (SELL)", "success"
            else: verdetto, colore = "🟡 TENERE (HOLD)", "warning"

            with cols_milano[i]:
                st.metric(label=f"{nome} ({ticker})", value=f"{prezzo_in_euro:.2f} €", delta=f"{var_giornaliera_milano:+.2f}%")
                st.markdown(f"**Score:** `{score:+.2f}`")
                if colore == "error": st.error(f"STRATEGIA: {verdetto}")
                elif colore == "success": st.success(f"STRATEGIA: {verdetto}")
                else: st.warning(f"STRATEGIA: {verdetto}")
    except Exception:
        cols_milano[i].error(f"Errore {nome}")

st.caption(f"Ultimo controllo eseguito il: {datetime.now().strftime('%d/%m/%Y alle %H:%M:%S')}")
