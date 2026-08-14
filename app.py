import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import time

# 1. Configurazione obbligatoria della pagina in cima allo script
st.set_page_config(page_title="Monitor Live Borsa Milano", page_icon="🏛️", layout="wide")

# Autorefresh automatico dello schermo impostato a 30 secondi
st_autorefresh(interval=30000, key="realtime_milano_refresh")

def estrai_prezzo_veloce(ticker_simbolo):
    """
    Interroga il modulo rapido dei server finanziari.
    Restituisce il prezzo dell'ultimo secondo reale senza caricare i grafici ritardati.
    """
    try:
        t = yf.Ticker(ticker_simbolo)
        
        # Interrogazione diretta ai parametri flash del server (zero ritardo)
        prezzo_corrente = float(t.fast_info['last_price'])
        chiusura_precedente = float(t.fast_info['previous_close'])
        
        if prezzo_corrente > 0 and chiusura_precedente > 0:
            variazione_percentuale = ((prezzo_corrente - chiusura_precedente) / chiusura_precedente) * 100
            return prezzo_corrente, variazione_percentuale
            
    except Exception:
        # Sottosistema di recupero d'emergenza se i parametri flash sono temporaneamente offline
        try:
            df = t.history(period="1d", interval="1m")
            if df is not None and not df.empty:
                prezzo_corrente = float(df['Close'].iloc[-1])
                chiusura_precedente = float(t.history(period="2d", interval="1d")['Close'].iloc[-2])
                variazione_percentuale = ((prezzo_corrente - chiusura_precedente) / chiusura_precedente) * 100
                return prezzo_corrente, variazione_percentuale
        except Exception:
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

# Interrogazione di STM con il suo ticker ufficiale di Milano
prezzo_stm, var_stm = estrai_prezzo_veloce("STMMI.MI")

# 🛑 PAUSA DI SICUREZZA: Evita che Yahoo veda due richieste nello stesso millisecondo dallo stesso IP
time.sleep(1.2)

# Interrogazione di Leonardo con il suo ticker ufficiale di Milano
prezzo_ldo, var_ldo = estrai_prezzo_veloce("LDO.MI")

# Soglia limite percentuale per l'allarme visivo (3.5%)
SOGLIA_ALLARME = 3.5

# Creazione del Layout a due colonne stabili
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
        st.info("🔄 Ricezione dati dal feed di Milano in corso...")

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
        st.info("🔄 Ricezione dati dal feed di Milano in corso...")
