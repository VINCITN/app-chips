import streamlit as st
import yfinance as yf
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import time

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Monitor Real-Time Milano", page_icon="🏛️", layout="wide")

# Aggiornamento automatico dello schermo ogni 30 secondi
st_autorefresh(interval=30000, key="realtime_milano_refresh")

def estrai_prezzo_veloce_yahoo(ticker_simbolo):
    """
    Estrae il prezzo reale istantaneo interrogando i parametri rapidi del server Yahoo Finance.
    Questo metodo aggira i blocchi delle API a pagamento e i ritardi dei grafici.
    """
    try:
        t = yf.Ticker(ticker_simbolo)
        
        # Interrogazione diretta ai parametri veloci (zero ritardo sui canali Streamlit)
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

# Interrogazione di STM con il suo ticker corretto di Borsa Italiana
prezzo_stm, var_stm = estrai_prezzo_veloce_yahoo("STMMI.MI")

# Pausa di sicurezza tecnica per evitare blocchi IP simultanei
time.sleep(1.0)

# Interrogazione di Leonardo con il suo ticker corretto di Borsa Italiana
prezzo_ldo, var_ldo = estrai_prezzo_veloce_yahoo("LDO.MI")

# Soglia limite percentuale per l'allarme visivo (3.5%)
SOGLIA_ALLARME = 3.5

# Creazione del Layout a due colonne stabili
col_stm, col_ldo = st.columns(2)

with col_stm:
    st.header("🇮🇹 STMicroelectronics")
    if prezzo_stm > 0:
        if abs(var_stm) >= SOGLIA_ALLARME:
            st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU STM!** Oscillazione: {var_stm:+.2f}%")
        
        st.metric(label="Quotazione Real-Time (Yahoo Fast)", value=f"{prezzo_stm:.3f} €", delta=f"{var_stm:+.2f}%")
        
        if var_stm > 0:
            st.success(f"📈 Guadagno del **{var_stm:+.2f}%** rispetto a ieri.")
        elif var_stm < 0:
            st.error(f"📉 Perdita del **{var_stm:+.2f}%** rispetto a ieri.")
        else:
            st.warning("↕️ Titolo Invariato (0.00%)")
    else:
        st.info("🔄 Ricezione dati dal feed di Milano in corso...")

with col_ldo:
    st.header("🇮🇹 Leonardo SpA")
    if prezzo_ldo > 0:
        if abs(var_ldo) >= SOGLIA_ALLARME:
            st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU LEONARDO!** Oscillazione: {var_ldo:+.2f}%")
        
        st.metric(label="Quotazione Real-Time (Yahoo Fast)", value=f"{prezzo_ldo:.3f} €", delta=f"{var_ldo:+.2f}%")
        
        if var_ldo > 0:
            st.success(f"📈 Guadagno del **{var_ldo:+.2f}%** rispetto a ieri.")
        elif var_ldo < 0:
            st.error(f"📉 Perdita del **{var_ldo:+.2f}%** rispetto a ieri.")
        else:
            st.warning("↕️ Titolo Invariato (0.00%)")
    else:
        st.info("🔄 Ricezione dati dal feed di Milano in corso...")
