import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import requests

# 1. Configurazione della pagina
st.set_page_config(page_title="Monitor Robotizzato Chips V13", page_icon="🤖", layout="wide")

# Refresh automatico ogni 60 secondi
st_autorefresh(interval=60000, key="global_auto_robot_v18")

# Sessione di richiesta con intestazioni browser standard
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8'
}
session.headers.update(headers)

def prendi_prezzo_live(ticker_simbolo):
    """Recupera la quotazione robusta per i mercati italiani ed esteri eliminando gli zeri"""
    try:
        t = yf.Ticker(ticker_simbolo, session=session)
        
        # PASSO 1: Proviamo a scaricare i dati intraday recenti (più affidabili di fast_info su Milano)
        df_intraday = t.history(period="1d", interval="1m")
        if not df_intraday.empty:
            prezzo_attuale = float(df_intraday['Close'].iloc[-1])
            
            # Recuperiamo la chiusura di ieri per calcolare la variazione percentuale reale
            df_storico = t.history(period="2d", interval="1d")
            chiusura_ieri = float(df_storico['Close'].iloc[-2]) if len(df_storico) > 1 else prezzo_attuale
            
            if prezzo_attuale > 0:
                variazione = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
                return prezzo_attuale, variazione
                
        # PASSO 2: Sottosistema di backup se l'intraday è vuoto (es. a mercati chiusi di notte o weekend)
        df_storico = t.history(period="2d", interval="1d")
        if not df_storico.empty:
            prezzo_attuale = float(df_storico['Close'].iloc[-1])
            chiusura_ieri = float(df_storico['Close'].iloc[-2]) if len(df_storico) > 1 else prezzo_attuale
            if prezzo_attuale > 0:
                variazione = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
                return prezzo_attuale, variazione
    except Exception as e:
        pass
        
    return 0.0, 0.0

def analizza_notizie_geopolitiche():
    """Scansiona i feed senza mandare in blocco l'applicazione"""
    parole_crisi_chips = ["tariff", "sanction", "export ban", "china", "taiwan", "restriction", "trade war"]
    parole_difesa = ["nato", "military", "defense", "pentagon", "missile", "war", "escalation"]
    
    score_chips, score_difesa = 0, 0
    notizie_rilevate = []
    
    try:
        for t_simbolo in ["TSM", "NVDA"]:
            ticker = yf.Ticker(t_simbolo, session=session)
            notizie = ticker.news
            if notizie:
                for n in notizie[:2]:
                    titolo = n.get('title', '').lower()
                    link = n.get('link', '#')
                    fonte = n.get('publisher', 'Yahoo')
                    
                    if any(p in titolo for p in parole_crisi_chips):
                        score_chips -= 15
                        notizie_rilevate.append({"testo": f"⚠️ **{fonte}**: [{n.get('title')}]({link})"})
                    
                    if any(p in titolo for p in parole_difesa):
                        score_difesa += 15
                        notizie_rilevate.append({"testo": f"🪖 **{fonte}**: [{n.get('title')}]({link})"})
    except:
        pass
    return score_chips, score_difesa, notizie_rilevate

# --- INTERFACCIA CRUSCOTTO ---
st.title("🤖 Real-Time Automated Chips & Geopolitical Monitor")

fuso_roma = pytz.timezone("Europe/Rome")
ora_esatta = datetime.now(fuso_roma).strftime("%H:%M:%S")
data_esatta = datetime.now(fuso_roma).strftime("%d/%m/%Y")

st.info(f"🔄 **Ultimo aggiornamento automatico AI:** {data_esatta} - **{ora_esatta}** (Sincronizzato Live Milano/Global)")

if st.button("🔄 Forza Rinfresco Dati"):
    st.rerun()

# ================= SIDEBAR =================
peso_chips, peso_difesa, lista_notizie = analizza_notizie_geopolitiche()
st.sidebar.header("📰 Analizzatore Live USA & Asia")

if lista_notizie:
    st.sidebar.warning("⚠️ ATTENZIONE: Rilevate notizie geopolitiche.")
    for noti in lista_notizie[:5]:
        st.sidebar.markdown(noti["testo"])
else:
    st.sidebar.success("🟢 Flussi geopolitici stabili. Nessun dazio o escalation rilevata.")

# ================= 1. I COLOSSI MONDIALI =================
st.header("🇺🇸🌏 Driver Globali dei Semiconduttori")
giap1, giap2, giap3 = st.columns(3)

with giap1:
    p_nvda, v_nvda = prendi_prezzo_live("NVDA")
    st.subheader("NVIDIA Corp (USA)")
    st.metric(label="Prezzo attuale", value=f"$ {p_nvda:.2f}", delta=f"{v_nvda:.2f}%")

with giap2:
    p_tsm, v_tsm = prendi_prezzo_live("TSM")
    st.subheader("TSMC (Taiwan)")
    st.metric(label="Prezzo attuale", value=f"$ {p_tsm:.2f}", delta=f"{v_tsm:.2f}%")

with giap3:
    p_asml, v_asml = prendi_prezzo_live("ASML")
    st.subheader("ASML Holding (Olanda)")
    st.metric(label="Prezzo attuale", value=f"$ {p_asml:.2f}", delta=f"{v_asml:.2f}%")

indice_globale = (v_nvda + v_tsm + v_asml) / 3
st.write(f"📊 **Spinta Globale del Comparto:** {indice_globale:.2f}%")
st.markdown("---")

# ================= 2. BORSA DI MILANO =================
st.header("🇮🇹 Quotazioni Live Borsa di Milano")
col1, col2 = st.columns(2)

with col1:
    # Utilizziamo STMMI.MI o STM.MI - entrambi validi, ma STMMI.MI a volte è più stabile su Yahoo
    p_stm_eur, v_stm = prendi_prezzo_live("STMMI.MI")
    
    st.subheader("STMicroelectronics (STM.MI)")
    st.metric(label="Prezzo Live Milano", value=f"€ {p_stm_eur:.2f}", delta=f"{v_stm:.2f}%")
    score_stm = v_stm + (indice_globale * 0.6) + peso_chips
    st.write(f"Rating: **{score_stm:.2f}**")
    if score_stm < -5: st.error("🔴 EVITARE / VENDI")
    elif score_stm > 2.5: st.success("🟢 COMPRA")
    else: st.warning("🟡 TIENI")

with col2:
    p_ldo, v_ldo = prendi_prezzo_live("LDO.MI")
    st.subheader("Leonardo S.p.A. (LDO.MI)")
    st.metric(label="Prezzo Live Milano", value=f"€ {p_ldo:.2f}", delta=f"{v_ldo:.2f}%")
    score_ldo = v_ldo + peso_difesa
    st.write(f"Rating: **{score_ldo:.2f}**")
    if score_ldo > 8 or peso_difesa > 0: st.success("🟢 COMPRA")
    elif score_ldo < -4: st.error("🔴 VENDI")
    else: st.warning("🟡 TIENI")
