import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import time

# 1. Configurazione della pagina ottimizzata per Hugging Face Spaces
st.set_page_config(page_title="Monitor Live Borsa Milano", page_icon="🏛️", layout="wide")

# Autorefresh automatico dello schermo ogni 45 secondi
st_autorefresh(interval=45000, key="realtime_milano_refresh")

def interroga_borsa_realtime(ticker_simbolo):
    """Interroga direttamente i server finanziari per estrarre l'ultimo prezzo e la variazione percentuale"""
    try:
        t = yf.Ticker(ticker_simbolo)
        
        # Corretto: rimosso il parametro illegale cache=False che causava il blocco dell'applicazione
        df_live = t.history(period="1d", interval="1m")
        df_ieri = t.history(period="2d", interval="1d")
        
        if not df_live.empty and len(df_ieri) >= 1:
            prezzo_corrente = float(df_live['Close'].iloc[-1])
            chiusura_precedente = float(df_ieri['Close'].iloc[-2]) if len(df_ieri) > 1 else float(df_ieri['Close'].iloc[0])
            variazione_percentuale = ((prezzo_corrente - chiusura_precedente) / chiusura_precedente) * 100
            return prezzo_corrente, variazione_percentuale
    except Exception as e:
        # Se c'è un errore temporaneo di rete, restituisce i dati vuoti per non far crashare la schermata
        pass
    return 0.0, 0.0

# ==========================================
# INTERFACCIA APPLICAZIONE (STREAMLIT LAYOUT)
# ==========================================

ora_attuale = datetime.now(pytz.timezone('Europe/Rome')).strftime('%H:%M:%S')
st.title("🏛️ Monitor Istantaneo Piazza Affari")

# Pulsante per forzare manualmente l'interrogazione immediata della borsa
if st.button("🔄 Forza Aggiornamento Book"):
    st.rerun()

st.caption(f"Ultimo pacchetto dati elaborato da Milano alle ore: **{ora_attuale}**")
st.markdown("---")

# Interrogazione di STM
prezzo_stm, var_stm = interroga_borsa_realtime("STMMI.MI")

# 🛑 PAUSA TECNICA ANTI-BLOCCO: Evita richieste simultanee ravvicinate
time.sleep(1.5)

# Interrogazione di Leonardo
prezzo_ldo, var_ldo = interroga_borsa_realtime("LDO.MI")

# Soglia limite percentuale per far scattare l'allarme visivo di volatilità critica (3.5%)
SOGLIA_ALLARME = 3.5

# Creazione del Layout a due grandi colonne affiancate
col_stm, col_ldo = st.columns(2)

with col_stm:
    st.header("🇮🇹 STMicroelectronics")
    if prezzo_stm > 0:
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
