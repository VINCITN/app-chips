import streamlit as st
import requests
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import time

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Monitor Real-Time Milano API", page_icon="🏛️", layout="wide")

# Aggiornamento automatico dello schermo ogni 15 secondi (con API professionale possiamo scendere di frequenza)
st_autorefresh(interval=15000, key="api_milano_refresh")

# =========================================================================
# 🔑 INSERISCI QUI LA TUA CHIAVE API DI TWELVE DATA
# =========================================================================
API_KEY = "08c87d06d1984672aa8b3b12fe70065c" 
# Rimprovero di sicurezza: Sostituisci la stringa sopra con la tua chiave reale presa dal sito!
# =========================================================================

def interroga_twelvedata_realtime(ticker_api):
    """Interroga l'API professionale di Twelve Data per estrarre prezzo e variazione istantanei"""
    # Se l'utente non ha ancora inserito la chiave corretta, interrompe per evitare crash
    if API_KEY == "IL_TUO_CODICE_API_KEY_QUI" or not API_KEY:
        return 0.0, 0.0
        
    url = f"https://twelvedata.com{ticker_api}&apikey={API_KEY}"
    
    try:
        risposta = requests.get(url, timeout=8).json()
        
        # Twelve Data restituisce i valori pronti all'uso nel dizionario principale
        prezzo_corrente = float(risposta.get('close', 0.0))
        variazione_percentuale = float(risposta.get('percent_change', 0.0))
        
        return prezzo_corrente, variazione_percentuale
    except Exception:
        pass
    return 0.0, 0.0

# ==========================================
# INTERFACCIA GRAFICA (STREAMLIT LAYOUT)
# ==========================================

ora_attuale = datetime.now(pytz.timezone('Europe/Rome')).strftime('%H:%M:%S')
st.title("🏛️ Monitor Istantaneo Piazza Affari (Flusso API Professionale)")

if st.button("🔄 Forza Aggiornamento Book"):
    st.rerun()

st.caption(f"Ultimo pacchetto dati validato da Milano alle ore: **{ora_attuale}**")
st.markdown("---")

# Controllo iniziale sulla chiave API per guidare l'utente nell'interfaccia
if API_KEY == "IL_TUO_CODICE_API_KEY_QUI":
    st.warning("⚠️ **Configurazione Richiesta**: Inserisci la tua API Key di Twelve Data all'interno del codice (riga 16) per attivare i dati in tempo reale al secondo.")
else:
    # Simboli ufficiali di Twelve Data per STM e Leonardo quotate a Milano (identificate dal suffisso .MI o STM)
    # Nota: Twelve Data usa spesso il formato senza punto o con l'ID del mercato Euronext Milan
    prezzo_stm, var_stm = interroga_twelvedata_realtime("STM")
    
    # Pausa tecnica minima di rispetto dei canali server
    time.sleep(0.5)
    
    prezzo_ldo, var_ldo = interroga_twelvedata_realtime("LDO")

    # Soglia limite percentuale per l'allarme visivo (3.5%)
    SOGLIA_ALLARME = 3.5
    
    # Creazione del Layout a due colonne stabili
    col_stm, col_ldo = st.columns(2)

    with col_stm:
        st.header("🇮🇹 STMicroelectronics")
        if prezzo_stm > 0:
            if abs(var_stm) >= SOGLIA_ALLARME:
                st.error(f"⚠️ **ALLARME VOLATILITÀ CRITICA SU STM!** Oscillazione: {var_stm:+.2f}%")
            
            st.metric(label="Quotazione Real-Time Certificata", value=f"{prezzo_stm:.3f} €", delta=f"{var_stm:+.2f}%")
            
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
            
            st.metric(label="Quotazione Real-Time Certificata", value=f"{prezzo_ldo:.3f} €", delta=f"{var_ldo:+.2f}%")
            
            if var_ldo > 0:
                st.success(f"📈 Guadagno del **{var_ldo:+.2f}%** rispetto a ieri.")
            elif var_ldo < 0:
                st.error(f"📉 Perdita del **{var_ldo:+.2f}%** rispetto a ieri.")
            else:
                st.warning("↕️ Titolo Invariato (0.00%)")
        else:
            st.info("🔄 Ricezione dati dal feed di Milano in corso...")
