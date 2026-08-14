import streamlit as st
import yfinance as yf
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import time

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Monitor Live Piazza Affari", page_icon="🏛️", layout="wide")

# Aggiornamento automatico dello schermo ogni 30 secondi
st_autorefresh(interval=30000, key="realtime_milano_refresh")

def estrai_prezzo_veloce_yahoo(ticker_simbolo):
    """Estrae il prezzo reale istantaneo dai parametri rapidi del server Yahoo Finance"""
    try:
        t = yf.Ticker(ticker_simbolo)
        
        # Sfrutta il widget flash di Yahoo per catturare l'ultimo contratto
        prezzo_corrente = float(t.fast_info['last_price'])
        chiusura_precedente = float(t.fast_info['previous_close'])
        
        if prezzo_corrente > 0 and chiusura_precedente > 0:
            variazione_percentuale = ((prezzo_corrente - chiusura_precedente) / chiusura_precedente) * 100
            return prezzo_corrente, variazione_percentuale
    except Exception:
        pass
    return 0.0, 0.0

# ==========================================
# INTERFACCIA GRAFICA (STREAMLIT LAYOUT)
# ==========================================

ora_attuale = datetime.now(pytz.timezone('Europe/Rome')).strftime('%H:%M:%S')
st.title("🏛️ Monitor Istantaneo Piazza Affari")

if st.button("🔄 Forza Aggiornamento Book"):
    st.rerun()

st.caption(f"Ultimo pacchetto dati elaborato da Milano alle ore: **{ora_attuale}**")
st.markdown("---")

# Interrogazione del primo titolo (STM)
prezzo_stm, var_stm = estrai_prezzo_veloce_yahoo("STMMI.MI")

# Pausa di sicurezza per evitare blocchi IP
time.sleep(1.2)

# Interrogazione del secondo titolo (Leonardo)
prezzo_ldo, var_ldo = estrai_prezzo_veloce_yahoo("LDO.MI")

# Soglia limite per l'allarme di volatilità (3.5%)
SOGLIA_ALLARME = 3.5

# Creazione di due colonne affiancate stabili
col_stm, col_ldo = st.columns(2)

with col_stm:
    st.header("🇮🇹 STMicroelectronics")
    if prezzo_stm > 0:
        if abs(var_stm) >= SOGLIA_ALLARME:
            st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU STM!** Oscillazione: {var_stm:+.2f}%")
        
        st.metric(label="Quotazione Real-Time (Euronext)", value=f"{prezzo_stm:.3f} €", delta=f"{var_stm:+.2f}%")
        
        if var_stm > 0:
            st.success(f"📈 Il titolo sta guadagnando il **{var_stm:+.2f}%** rispetto a ieri.")
        elif var_stm < 0:
            st.error(f"📉 Il titolo sta perdendo il **{var_stm:+.2f}%** rispetto a ieri.")
        else:
            st.warning("↕️ Titolo Invariato (0.00%)")
    else:
        st.info("🔄 Ricezione dati dal feed di Milano in corso...")

with col_ldo:
    st.header("🇮🇹 Leonardo SpA")
    if prezzo_ldo > 0:
        if abs(var_ldo) >= SOGLIA_ALLARME:
            st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU LEONARDO!** Oscillazione: {var_ldo:+.2f}%")
        
        st.metric(label="Quotazione Real-Time (Euronext)", value=f"{prezzo_ldo:.3f} €", delta=f"{var_ldo:+.2f}%")
        
        if var_ldo > 0:
            st.success(f"📈 Il titolo sta guadagnando il **{var_ldo:+.2f}%** rispetto a ieri.")
        elif var_ldo < 0:
            st.error(f"📉 Il titolo sta perdendo il **{var_ldo:+.2f}%** rispetto a ieri.")
        else:
            st.warning("↕️ Titolo Invariato (0.00%)")
    else:
        st.info("🔄 Ricezione dati dal feed di Milano in corso...")

st.markdown("---")
