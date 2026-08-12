import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import requests

# 1. Configurazione della pagina (Deve essere la prima istruzione Streamlit)
st.set_page_config(page_title="Monitor Robotizzato Chips V13", page_icon="🤖", layout="wide")

# Refresh automatico ogni 60 secondi con una chiave nuova per azzerare i vecchi blocchi
st_autorefresh(interval=60000, key="global_auto_robot_v14")

# SESSIONE ANTI-BLOCCO: Evita che l'IP del server venga rifiutato da Yahoo Finance
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

def prendi_prezzo_live(ticker_simbolo):
    """Recupera la quotazione istantanea sul mercato senza ritardi strutturali"""
    try:
        t = yf.Ticker(ticker_simbolo, session=session)
        df_oggi = t.history(period="1d", interval="1m")
        if not df_oggi.empty:
            prezzo_attuale = float(df_oggi['Close'].iloc[-1])
            try:
                chiusura_ieri = t.info.get('previousClose', df_oggi['Close'].iloc[-1])
            except:
                chiusura_ieri = df_oggi['Close'].iloc
            variazione = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
            return prezzo_attuale, variazione
        else:
            info = t.info
            p = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            v = info.get('regularMarketChangePercent', 0.0)
            if 0 < v < 1:  
                v = v * 100
            return p, v
    except:
        return 0.0, 0.0

def analizza_notizie_geopolitiche():
    """Scansiona i feed USA/Asia di Yahoo Finance alla ricerca di dazi o tensioni economici"""
    parole_crisi_chips = [
        "tariff", "sanction", "export ban", "china", "taiwan", "restriction", 
        "trade war", "chips act", "white house", "biden", "trump", "beijing"
    ]
    parole_difesa = ["nato", "military", "defense", "pentagon", "spending", "missile", "war", "escalation"]
    
    score_chips = 0
    score_difesa = 0
    notizie_rilevate = []
    
    try:
        for t_simbolo in ["TSM", "NVDA"]:
            ticker = yf.Ticker(t_simbolo, session=session)
            notizie = ticker.news
            if notizie:
                for n in notizie[:5]:
                    titolo = n.get('title', '').lower()
                    link = n.get('link', '#')
                    fonte = n.get('publisher', 'Yahoo Finance')
                    
                    if any(p in titolo for p in parole_crisi_chips):
                        score_chips -= 15
                        if n.get('title') not in [x.get('testo') for x in notizie_rilevate]:
                            notizie_rilevate.append({
                                "testo": f"⚠️ **{fonte}**: [{n.get('title')}]({link})",
                                "tipo": "chips"
                            })
                    
                    if any(p in titolo for p in parole_difesa):
                        score_difesa += 15
                        if n.get('title') not in [x.get('testo') for x in notizie_rilevate]:
                            notizie_rilevate.append({
                                "testo": f"🪖 **{fonte}**: [{n.get('title')}]({link})",
                                "tipo": "difesa"
                            })
    except:
        pass
        
    return score_chips, score_difesa, notizie_rilevate

# --- INTERFACCIA CRUSCOTTO ---
st.title("🤖 Real-Time Automated Chips & Geopolitical Monitor")

# Rilevamento dinamico dell'ora ad ogni ciclo, senza blocchi di cache
fuso_roma = pytz.timezone("Europe/Rome")
ora_esatta = datetime.now(fuso_roma).strftime("%H:%M:%S")
data_esatta = datetime.now(fuso_roma).strftime("%d/%m/%Y")

st.info(f"🔄 **Ultimo aggiornamento automatico AI:** {data_esatta} - **{ora_esatta}** (Sincronizzato Live)")

# Pulsante manuale nel caso in cui tu voglia forzare il caricamento istantaneo
if st.button("🔄 Forza Rinfresco Dati"):
    st.rerun()

# ================= SIDEBAR: MONITOR NOTIZIE AUTOMATICO =================
peso_chips, peso_difesa, lista_notizie = analizza_notizie_geopolitiche()

st.sidebar.header("📰 Analizzatore Live USA & Asia")
st.sidebar.write("L'algoritmo scansiona i feed di Yahoo Finance.")

if lista_notizie:
    if len(lista_notizie) >= 3:
        st.sidebar.error("🚨 ALERT: Rilevato forte accumulo di notizie macroeconomiche/tensioni!")
    else:
        st.sidebar.warning("⚠️ ATTENZIONE: Rilevate notizie geopolitiche di rilievo.")
        
    st.sidebar.write("### Ultime notizie rilevate:")
    for noti in lista_notizie[:5]:
        st.sidebar.markdown(noti["testo"])
else:
    st.sidebar.success("🟢 Flussi geopolitici stabili. Nessun dazio o escalation rilevata nei feed attuali.")

# ================= 1. I COLOSSI MONDIALI (USA & ASIA) =================
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
st.write(f"📊 **Spinta Globale del Comparto:** Mediamente i colossi si muovono del **{indice_globale:.2f}%**.")

st.markdown("---")

# ================= 2. BORSA DI MILANO =================
st.header("🇮🇹 Quotazioni Live Borsa di Milano")

col1, col2 = st.columns(2)

with col1:
    p_stm, v_stm = prendi_prezzo_live("STM.MI")
    st.subheader("STMicroelectronics (STM.MI)")
    st.metric(label="Prezzo Live Milano", value=f"€ {p_stm:.2f}", delta=f"{v_stm:.2f}%")
    
    score_stm = v_stm + (indice_globale * 0.6) + peso_chips
    st.write(f"Rating di Flusso Automatizzato: **{score_stm:.2f}**")
    
    if score_stm < -5:
        st.error("🔴 EVITARE / VENDI")
    elif score_stm > 2.5:
        st.success("🟢 COMPRA")
    else:
        st.warning("🟡 TIENI")

with col2:
    p_ldo, v_ldo = prendi_prezzo_live("LDO.MI")
    st.subheader("Leonardo S.p.A. (LDO.MI)")
    st.metric(label="Prezzo Live Milano", value=f"€ {p_ldo:.2f}", delta=f"{v_ldo:.2f}%")
    
    score_ldo = v_ldo + peso_difesa
    st.write(f"Rating di Flusso Automatizzato: **{score_ldo:.2f}**")
    
    if score_ldo > 8 or peso_difesa > 0:
        st.success("🟢 COMPRA")
    elif score_ldo < -4:
        st.error("🔴 VENDI")
    else:
        st.warning("🟡 TIENI")
