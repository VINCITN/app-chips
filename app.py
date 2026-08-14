import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import requests
import time
import random

# 1. Configurazione della pagina ottimizzata per Hugging Face Spaces
st.set_page_config(page_title="Monitor Live Borsa Milano", page_icon="🏛️", layout="wide")

# Autorefresh automatico dello schermo ogni 45 secondi (evita blocchi da richieste troppo frequenti)
st_autorefresh(interval=45000, key="realtime_milano_refresh")

def genera_sessione_anti_blocco():
    """Crea una sessione con intestazioni browser variabili per bypassare i filtri anti-bot"""
    session = requests.Session()
    
    # Rotazione degli User-Agent per simulare browser reali diversi
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Origin': 'https://yahoo.com',
        'Referer': 'https://yahoo.com/'
    }
    session.headers.update(headers)
    return session

def interroga_borsa_realtime(ticker_simbolo, sessione):
    """Interroga direttamente i server finanziari per estrarre l'ultimo prezzo e la variazione percentuale"""
    try:
        t = yf.Ticker(ticker_simbolo, session=sessione)
        
        # cache=False forza il server a restituire l'ultimo secondo reale senza dati memorizzati vecchio stile
        df_live = t.history(period="1d", interval="1m", cache=False)
        df_ieri = t.history(period="2d", interval="1d", cache=False)
        
        if not df_live.empty and len(df_ieri) >= 1:
            prezzo_corrente = float(df_live['Close'].iloc[-1])
            chiusura_precedente = float(df_ieri['Close'].iloc[-2]) if len(df_ieri) > 1 else float(df_ieri['Close'].iloc)
            variazione_percentuale = ((prezzo_corrente - chiusura_precedente) / chiusura_precedente) * 100
            return prezzo_corrente, variazione_percentuale
    except Exception:
        pass
    return 0.0, 0.0

# ==========================================
# INTERFACCIA APPLICAZIONE (STREAMLIT LAYOUT)
# ==========================================

# Orario dinamico di Roma aggiornato al secondo
ora_attuale = datetime.now(pytz.timezone('Europe/Rome')).strftime('%H:%M:%S')
st.title("🏛️ Monitor Istantaneo Piazza Affari")

# Pulsante per forzare manualmente l'interrogazione immediata della borsa
if st.button("🔄 Forza Aggiornamento Book"):
    st.rerun()

st.caption(f"Ultimo pacchetto dati elaborato da Milano alle ore: **{ora_attuale}**")
st.markdown("---")

# Generiamo una sessione fresca e pulita per questa specifica richiesta
sessione_attiva = genera_sessione_anti_blocco()

# Interrogazione di STM
prezzo_stm, var_stm = interroga_borsa_realtime("STMMI.MI", sessione_attiva)

# 🛑 PAUSA TECNICA ANTI-BLOCCO: Aspettiamo poco più di un secondo prima della richiesta successiva
# Impedisce a Yahoo di intercettare due richieste simultanee dallo stesso server di Hugging Face
time.sleep(1.2)

# Interrogazione di Leonardo
prezzo_ldo, var_ldo = interroga_borsa_realtime("LDO.MI", sessione_attiva)

# Soglia limite percentuale per far scattare l'allarme visivo di volatilità critica (3.5%)
SOGLIA_ALLARME = 3.5

# Creazione del Layout a due grandi colonne affiancate
col_stm, col_ldo = st.columns(2)

with col_stm:
    st.header("🇮🇹 STMicroelectronics")
    if prezzo_stm > 0:
        # Controllo e attivazione dell'allarme critico
        if abs(var_stm) >= SOGLIA_ALLARME:
            st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU STM!** Oscillazione: {var_stm:+.2f}%")
        
        st.metric(label="Quotazione Real-Time", value=f"{prezzo_stm:.3f} €", delta=f"{var_stm:+.2f}%")
        
        if var_stm > 0:
            st.success(f"📈 Guadagno del **{var_stm:+.2f}%** rispetto a ieri.")
        elif var_stm < 0:
            st.error(f"📉 Perdita del **{var_stm:+.2f}%** rispetto a ieri.")
        else:
            st.warning("↕️ Titolo Invariato (0.00%)")
    else:
        st.info("🔄 Tentativo di riconnessione al server di Milano in corso...")

with col_ldo:
    st.header("🇮🇹 Leonardo SpA")
    if prezzo_ldo > 0:
        # Controllo e attivazione dell'allarme critico
        if abs(var_ldo) >= SOGLIA_ALLARME:
            st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU LEONARDO!** Oscillazione: {var_ldo:+.2f}%")
        
        st.metric(label="Quotazione Real-Time", value=f"{prezzo_ldo:.3f} €", delta=f"{var_ldo:+.2f}%")
        
        if var_ldo > 0:
            st.success(f"📈 Guadagno del **{var_ldo:+.2f}%** rispetto a ieri.")
        elif var_ldo < 0:
            st.error(f"📉 Perdita del **{var_ldo:+.2f}%** rispetto a ieri.")
        else:
            st.warning("↕️ Titolo Invariato (0.00%)")
    else:
        st.info("🔄 Tentativo di riconnessione al server di Milano in corso...")
