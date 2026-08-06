from datetime import datetime, timedelta
import time
import numpy as np
import pandas as pd
import requests_cache
import streamlit as st
import yfinance as yf

# --- CONFIGURAZIONE CACHE E SICUREZZA ---
if "session" not in st.session_state:
    st.session_state.session = requests_cache.CachedSession(
        "yf_security_lock.cache", expire_after=120
    )

if "ultimo_aggiornamento_reale" not in st.session_state:
    st.session_state.ultimo_aggiornamento_reale = (
        datetime.now() - timedelta(minutes=5)
    )

st.set_page_config(page_title="Crypto & Chip Dashboard", layout="wide")

# --- BARRA LATERALE CON TIMER E CONTROLLO ---
with st.sidebar:
    st.header("⏱️ Stato Connessione API")
    ora_attuale = datetime.now()
    secondi_passati = (
        ora_attuale - st.session_state.ultimo_aggiornamento_reale
    ).total_seconds()
    secondi_mancanti = max(0, int(120 - secondi_passati))

    if secondi_mancanti > 0:
        st.metric(
            label="Prossimo aggiornamento sicuro tra:",
            value=f"{secondi_mancanti} secondi",
        )
        st.info("🔄 Lettura automatica da memoria cache locale.")
    else:
        st.success("🟢 Server pronti per una richiesta diretta!")

    st.markdown("---")
    if st.button("⚡ BYPASS CACHE: Tempo Reale Ora"):
        st.toast("Richiesta immediata dati freschi a Yahoo Finance.")
        st.session_state.session.cache.clear()
        st.session_state.ultimo_aggiornamento_reale = datetime.now()
        st.rerun()

st.title("📊 Dashboard Algoritmica Semiconduttori & Geopolitica")
st.write(
    "Incrocio dati di mercato, indicatori di analisi tecnica e impatto delle politiche USA-Asia."
)


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


# --- TICKERS DI MERCATO ---
TITOLI_MILANO = {"STM.MI": "STMicroelectronics", "LDO.MI": "Leonardo S.p.A."}
TICKERS_CHIPS = {
    "NVDA": "NVIDIA (USA)",
    "TSM": "TSMC (Asia)",
    "ASML": "ASML (Europa)",
}
TICKERS_GEOPOLITICA = {
    "^VIX": "Indice Incertezza (VIX)",
    "ITA": "Fondo Difesa Globale (iShares)",
}

if secondi_mancanti == 0:
    st.session_state.ultimo_aggiornamento_reale = datetime.now()

# --- 1. COMPARTO CHIP INTERNAZIONALE ---
st.subheader("🌐 Comparto Chip Internazionale")
cols_chips = st.columns(3)
somma_var_chips, conteggio_chips = 0, 0

for i, (ticker, nome) in enumerate(TICKERS_CHIPS.items()):
    try:
        t = yf.Ticker(ticker, session=st.session_state.session)
        df = t.history(period="5d")
        if len(df) >= 2:
            prezzo_attuale = df["Close"].iloc[-1]
            chiusura_ieri = df["Close"].iloc[-2]
            var = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
            somma_var_chips += var
            conteggio_chips += 1
            cols_chips[i].metric(
                label=nome, value=f"{prezzo_attuale:.2f} USD", delta=f"{var:+.2f}%"
            )
    except Exception:
        cols_chips[i].error(f"Errore {nome}")

momentum_chips_globale = (
    somma_var_chips / conteggio_chips if conteggio_chips > 0 else 0
)

# --- 2. SCENARIO GEOPOLITICO INTERNAZIONALE ---
st.subheader("⚔️ Scenario Geopolitico Internazionale")
cols_geo = st.columns(2)
var_vix, var_difesa = 0.0, 0.0

for i, (ticker, nome) in enumerate(TICKERS_GEOPOLITICA.items()):
    try:
        t = yf.Ticker(ticker, session=st.session_state.session)
        df = t.history(period="5d")
        if len(df) >= 2:
            prezzo_attuale = df["Close"].iloc[-1]
            chiusura_ieri = df["Close"].iloc[-2]
            var = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
            cols_geo[i].metric(
                label=nome, value=f"{prezzo_attuale:.2f}", delta=f"{var:+.2f}%"
            )
            if ticker == "^VIX":
                var_vix = var
            elif ticker == "ITA":
                var_difesa = var
    except Exception:
        cols_geo[i].error(f"Errore {nome}")

# --- 3. SEGNALI OPERATIVI ED ANALISI TECNICA ---
st.subheader("🇮🇹 Analisi Tecnica Avanzata & Segnali Milano (EURO)")

for ticker, nome in TITOLI_MILANO.items():
    st.write(f"### 📈 Analisi Tecnica: **{nome} ({ticker})**")
    try:
        t = yf.Ticker(ticker, session=st.session_state.session)
        df = t.history(period="6mo")

        if len(df) >= 50:
            df["SMA20"] = calcola_sma(df["Close"], window=20)
            df["SMA50"] = calcola_sma(df["Close"], window=50)
            df["RSI"] = calcola_rsi(df["Close"], window=14)

            prezzo_attuale = df["Close"].iloc[-1]
            apertura_oggi = df["Open"].iloc[-1]
            var_giornaliera = (
                (prezzo_attuale - apertura_oggi) / apertura_oggi
            ) * 100

            ultimo_rsi = df["RSI"].iloc[-1]
            ultima_sma20 = df["SMA20"].iloc[-1]
            ultima_sma50 = df["SMA50"].iloc[-1]

            if "STM" in ticker:
                score_geo = (
                    (var_giornaliera * 0.5)
                    + (momentum_chips_globale * 0.4)
                    - (var_vix * 0.1)
                )
                soglia_buy, soglia_sell = 0.4, -0.4
            else:
                score_geo = (
                    (var_giornaliera * 0.5)
                    + (var_difesa * 0.3)
                    + (var_vix * 0.2)
                )
                soglia_buy, soglia_sell = 0.3, -0.3

            trend_rialzista = (
                prezzo_attuale > ultima_sma20 and ultima_sma20 > ultima_sma50
            )

            if score_geo > soglia_buy:
                if ultimo_rsi >= 70:
                    verdetto, colore = (
                        "🟡 HOLD (Score positivo ma RSI in Ipercomprato!)",
                        "warning",
                    )
                elif not trend_rialzista:
                    verdetto, colore = (
                        "🟡 HOLD (Score positivo ma Trend sotto le Medie)",
                        "warning",
                    )
                else:
                    verdetto, colore = (
                        "🟢 COMPRARE (BUY) - Geopolitica + Tecnica OK",
                        "success",
                    )
            elif score_geo < soglia_sell:
                if ultimo_rsi <= 30:
                    verdetto, colore = (
                        "🟡 HOLD (Score negativo ma RSI in Ipervenduto!)",
                        "warning",
                    )
                else:
                    verdetto, colore = (
                        "🔴 VENDERE (SELL) - Segnale di scarico",
                        "error",
                    )
            else:
                verdetto, colore = (
                    "🟡 TENERE (HOLD) - Equilibrio di mercato",
                    "warning",
                )

            col1, col2, col3, col4 = st.columns(4)
            col1.metric(
                label="Prezzo Ultima Chiusura",
                value=f"{prezzo_attuale:.2f} €",
                delta=f"{var_giornaliera:+.2f}%",
            )
            col2.metric(
                label="RSI (14 giorni)",
                value=f"{ultimo_rsi:.1f}",
                delta="Ipercomprato"
                if ultimo_rsi > 70
                else ("Ipervenduto" if ultimo_rsi < 30 else "Neutro"),
            )
            col3.metric(
                label="Media Mobile Breve (SMA 20)",
                value=f"{ultima_sma20:.2f} €",
            )
            col4.metric(
                label="Media Mobile Lunga (SMA 50)",
                value=f"{ultima_sma50:.2f} €",
            )

            if colore == "success":
                st.success(f"STRATEGIA EMESSA: {verdetto}")
            elif colore == "error":
                st.error(f"STRATEGIA EMESSA: {verdetto}")
            else:
                st.warning(f"STRATEGIA EMESSA: {verdetto}")

            chart_df = df[["Close", "SMA20", "SMA50"]].tail(60)
            st.line_chart(chart_df)
            st.markdown("---")
    except Exception as e:
        st.error(f"Impossibile analizzare il titolo {nome}. Errore: {e}")


# --- 4. PANNELLO DECISIONI GEOPOLITICHE ED ECONOMICHE USA & ASIA ---
st.subheader("🇺🇸 🇨🇳 Monitor Geopolitico ed Economico Attuale (USA & Asia)")

with st.expander("🔍 Clicca per espandere il Focus sulle Politiche in Corso", expanded=True):
    geo_col1, geo_col2 = st.columns(2)

    with geo_col1:
        st.markdown("### 🇺🇸 Politiche ed Economia Stati Uniti")
        st.info(
            "**1. Tariffe Section 232 sui Chip AI (25%)**\n\n"
            "L'amministrazione Trump ha attivato tariffe del 25% su processori avanzati (es. NVIDIA H200) esportati in Asia. "
            "Questo altera i flussi di fatturato dei big tech americani e congestiona la catena logistica di fonderia globale.\n\n"
            "**2. Nuova Tariffa del 15% sul Polisilicio**\n\n"
            "Gli USA stanno introducendo barriere doganali e prezzi minimi per l'importazione di polisilicio e wafer grezzi. "
            "L'obiettivo è proteggere le fabbriche interne, ma ciò causa una forte pressione sul costo delle materie prime per i produttori occidentali."
        )
        # Analisi dell'impatto numerico reale misurato nella sezione sopra
        if var_vix > 1.5:
            st.warning(
                f"⚠️ **Rilevazione Quantitativa**: L'incertezza sul mercato USA sta salendo (VIX: {var_vix:+.2f}%). "
                "Questo aumento penalizza l'algoritmo di STM e rallenta l'afflusso di capitali sul tech europeo."
            )
        else:
            st.success(
