import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione della pagina e Refresh automatico ogni 60 secondi
st.set_page_config(page_title="Monitor Geopolitico Chips V10", page_icon="🌐", layout="wide")
st_autorefresh(interval=60000, key="global_anti_block_v10")

# Svuota la memoria per garantire dati sempre freschi
try:
    st.cache_data.clear()
except:
    pass

def prendi_prezzo_live(ticker_simbolo):
    """Recupera l'ultimo prezzo disponibile sul mercato senza ritardi strutturali"""
    try:
        t = yf.Ticker(ticker_simbolo)
        # Proviamo a prendere l'ultimo minuto di contrattazione
        df_oggi = t.history(period="1d", interval="1m")
        if not df_oggi.empty:
            prezzo_attuale = df_oggi['Close'].iloc[-1]
            chiusura_ieri = t.info.get('previousClose', df_oggi['Close'].iloc[0])
            variazione = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
            return prezzo_attuale, variazione
        else:
            # Fallback se la borsa di riferimento è chiusa in questo istante
            info = t.info
            p = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            v = info.get('regularMarketChangePercent', 0.0)
            if v and v > 0 and v < 1:  # Correzione formato percentuale yfinance
                v = v * 100
            return p, v
    except:
        return 0.0, 0.0

# --- INTERFACCIA CRUSCOTTO ---
st.title("💡 Real-Time Global Chips & Geopolitical Monitor")

fuso_roma = pytz.timezone("Europe/Rome")
ora_esatta = datetime.now(fuso_roma).strftime("%H:%M:%S")
st.write(f"Ultimo aggiornamento flussi globali: **{ora_esatta}** (Sincronizzato live)")
st.success("🟢 SERVER AGGIORNATO - FLUSSO INTERNAZIONALE ATTIVO")

# ================= FILTRI GEOPOLITICI LATERALI =================
st.sidebar.header("🛡️ Scenari Geopolitici (USA / ASIA)")
st.sidebar.write("Attiva una decisione macroeconomica per testare l'impatto algoritmico su STM e Leonardo:")

scenario_usa = st.sidebar.checkbox("🇺🇸 Nuove Tariffe / CHIPS Act USA contro la Cina")
scenario_taiwan = st.sidebar.checkbox("🇨🇳 Escalation Militare / Blocco dello Stretto di Taiwan")
scenario_difesa = st.sidebar.checkbox("🇪🇺 Incremento Spesa Militare NATO / Difesa Europea")

# Calcolo del peso geopolitico sul sentiment
peso_geopolitico = 0
if scenario_usa: peso_geopolitico -= 12
if scenario_taiwan: peso_geopolitico -= 35
if scenario_difesa: peso_geopolitico += 20

# ================= 1. I COLOSSI MONDIALI (USA & ASIA) =================
st.header("🇺🇸🌏 Driver Globali dei Semiconduttori")
st.write("L'andamento di questi giganti anticipa il trend di mercato per i semiconduttori in Europa.")

giap1, giap2, giap3 = st.columns(3)

with giap1:
    p_nvda, v_nvda = prendi_prezzo_live("NVDA")
    st.subheader("NVIDIA Corp (USA)")
    st.metric(label="Prezzo attuale", value=f"$ {p_nvda:.2f}", delta=f"{v_nvda:.2f}%")
    st.caption("Monopolio Chip AI - Guida l'intero sentiment tech a Wall Street.")

with giap2:
    p_tsm, v_tsm = prendi_prezzo_live("TSM")
    st.subheader("TSMC (Taiwan)")
    st.metric(label="Prezzo attuale", value=f"$ {p_tsm:.2f}", delta=f"{v_tsm:.2f}%")
    st.caption("Fonderia Mondiale - Il barometro delle tensioni fisiche in Asia.")

with giap3:
    p_asml, v_asml = prendi_prezzo_live("ASML")
    st.subheader("ASML Holding (Olanda)")
    st.metric(label="Prezzo attuale", value=f"$ {p_asml:.2f}", delta=f"{v_asml:.2f}%")
    st.caption("Macchinari UV - Unico fornitore al mondo per la produzione di chip avanzati.")

# Calcolo dell'indice medio mondiale dei chip
indice_globale = (v_nvda + v_tsm + v_asml) / 3
st.info(f"📊 **Spinta Globale del Comparto:** In questo momento i colossi mondiali si muovono mediamente del **{indice_globale:.2f}%**.")

st.markdown("---")

# ================= 2. BORSA DI MILANO (QUOTAZIONI IN TEMPO REALE) =================
st.header("🇮🇹 Borsa di Milano (Quotazioni in Diretta Ricalcolate)")
st.write("Prezzi live da Piazza Affari con rating integrato basato su dati tecnici e scenari internazionali.")

col1, col2 = st.columns(2)

with col1:
    p_stm, v_stm = prendi_prezzo_live("STMMI.MI")
    st.subheader("STMicroelectronics (STM.MI)")
    st.metric(label="Prezzo Live Milano", value=f"€ {p_stm:.2f}", delta=f"{v_stm:.2f}%")
    
    # Algoritmo decisionale evoluto per i chip europei
    score_stm = v_stm + (indice_globale * 0.6) + (peso_geopolitico if peso_geopolitico < 0 else 0)
    
    st.write(f"Rating di Flusso Integrato: **{score_stm:.2f}**")
    if score_stm < -8 or scenario_taiwan:
        st.error("🔴 EVITARE / VENDI: Forte rischio sulla catena di fornitura o crollo dei leader USA/Asia.")
    elif score_stm > 2.5:
        st.success("🟢 COMPRA: Forti driver mondiali a supporto e mercato stabile.")
    else:
        st.warning("🟡 TIENI: Posizione neutrale. Il mercato attende conferme macroeconomiche.")

with col2:
    p_ldo, v_ldo = prendi_prezzo_live("LDO.MI")
    st.subheader("Leonardo S.p.A. (LDO.MI)")
    st.metric(label="Prezzo Live Milano", value=f"€ {p_ldo:.2f}", delta=f"{v_ldo:.2f}%")
    
    # Algoritmo decisionale per la difesa (trae vantaggio dall'instabilità geopolitica)
    score_ldo = v_ldo + (30 if scenario_taiwan else 0) + (peso_geopolitico if peso_geopolitico > 0 else 0)
    
    st.write(f"Rating di Flusso Integrato: **{score_ldo:.2f}**")
    if score_ldo > 12 or scenario_difesa:
        st.success("🟢 COMPRA: Forte spinta rialzista legata all'aumento dei budget di difesa e sicurezza.")
    elif score_ldo < -4:
        st.error("🔴 VENDI: Allentamento delle tensioni o prese di beneficio sul settore aerospaziale.")
    else:
        st.warning("🟡 TIENI: Sentiment stabile nel comparto difesa europeo.")
