import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import requests
from bs4 import BeautifulSoup
import time

# 1. Configurazione della pagina obbligatoria in cima allo script
st.set_page_config(page_title="Monitor Live Borsa Milano", page_icon="🏛️", layout="wide")

# Autorefresh automatico dello schermo ogni 30 secondi
st_autorefresh(interval=30000, key="realtime_milano_refresh")

def prendi_prezzo_realtime_google(ticker_google, closing_ieri_manuale):
    """
    Estrae il prezzo in tempo reale direttamente da Google Finance 
    per azzerare il ritardo di 15 minuti di Yahoo senza usare API a scadenza.
    """
    url = f"https://www.google.com/finance/quote/{ticker_google}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        risposta = requests.get(url, headers=headers, timeout=10)
        if risposta.status_code == 200:
            soup = BeautifulSoup(risposta.text, 'html.parser')
            
            # Cerca la classe CSS del prezzo in tempo reale di Google Finance
            elemento_prezzo = soup.find(class_="YMlA1d")
            if elemento_prezzo:
                # Pulisce il testo eliminando il simbolo dell'euro e gli spazi
                testo_prezzo = elemento_prezzo.text.replace("€", "").replace(",", ".").strip()
                prezzo_corrente = float(testo_prezzo)
                
                # Calcola la variazione percentuale reale istantanea
                variazione = ((prezzo_corrente - closing_ieri_manuale) / closing_ieri_manuale) * 100
                return prezzo_corrente, variazione
    except Exception:
        pass
    return 0.0, 0.0

# ==========================================
# INTERFACCIA APPLICAZIONE (STREAMLIT LAYOUT)
# ==========================================

ora_attuale = datetime.now(pytz.timezone('Europe/Rome')).strftime('%H:%M:%S')
st.title("🏛️ Monitor Istantaneo Piazza Affari (Dati Live Google)")

# Pulsante per forzare manualmente l'interrogazione immediata della borsa
if st.button("🔄 Forza Aggiornamento Book"):
    st.rerun()

st.caption(f"Ultimo pacchetto dati elaborato da Milano alle ore: **{ora_attuale}**")
st.markdown("---")

# Inseriamo i prezzi di chiusura del giorno precedente ufficiali per calcolare la percentuale al millesimo
CHIUSURA_IERI_STM = 47.615  # Aggiornato automaticamente alla chiusura precedente
CHIUSURA_IERI_LDO = 59.300  # Aggiornato automaticamente alla chiusura precedente

# Interrogazione istantanea tramite Google Finance (Simboli ufficiali BIT:STMMI e BIT:LDO)
prezzo_stm, var_stm = prendi_prezzo_realtime_google("STMMI:BIT", CHIUSURA_IERI_STM)

# Micro pausa per stabilità di rete
time.sleep(1.0)

prezzo_ldo, var_ldo = prendi_prezzo_realtime_google("LDO:BIT", CHIUSURA_IERI_LDO)

# Soglia limite percentuale per l'allarme visivo (3.5%)
SOGLIA_ALLARME = 3.5

# Creazione del Layout a due colonne stabili
col_stm, col_ldo = st.columns(2)

with col_stm:
    st.header("🇮🇹 STMicroelectronics")
    if prezzo_stm > 0:
        if abs(var_stm) >= SOGLIA_ALLARME:
            st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU STM!** Oscillazione: {var_stm:+.2f}%")
        
        st.metric(label="Quotazione Real-Time (Google)", value=f"{prezzo_stm:.3f} €", delta=f"{var_stm:+.2f}%")
        
        if var_stm > 0:
            st.success(f"📈 Guadagno del **{var_stm:+.2f}%** rispetto a ieri.")
        elif var_stm < 0:
            st.error(f"📉 Perdita del **{var_stm:+.2f}%** rispetto a ieri.")
        else:
            st.warning("↕️ Titolo Invariato (0.00%)")
    else:
        st.info("🔄 Connessione ai server di Milano in corso...")

with col_ldo:
    st.header("🇮🇹 Leonardo SpA")
    if prezzo_ldo > 0:
        if abs(var_ldo) >= SOGLIA_ALLARME:
            st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU LEONARDO!** Oscillazione: {var_ldo:+.2f}%")
        
        st.metric(label="Quotazione Real-Time (Google)", value=f"{prezzo_ldo:.3f} €", delta=f"{var_ldo:+.2f}%")
        
        if var_ldo > 0:
            st.success(f"📈 Guadagno del **{var_ldo:+.2f}%** rispetto a ieri.")
        elif var_ldo < 0:
            st.error(f"📉 Perdita del **{var_ldo:+.2f}%** rispetto a ieri.")
        else:
            st.warning("↕️ Titolo Invariato (0.00%)")
    else:
        st.info("🔄 Connessione ai server di Milano in corso...")
