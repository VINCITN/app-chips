import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 1. Configurazione della pagina e Refresh automatico ogni 60 secondi
st.set_page_config(page_title="Monitor Robotizzato Chips V13", page_icon="🤖", layout="wide")
st_autorefresh(interval=60000, key="global_auto_robot_v13")

# Svuota la cache per garantire dati e notizie sempre aggiornati al minuto
try:
    st.cache_data.clear()
except:
    pass

def prendi_prezzo_live(ticker_simbolo):
    """Recupera la quotazione istantanea sul mercato senza ritardi strutturali"""
    try:
        t = yf.Ticker(ticker_simbolo)
        df_oggi = t.history(period="1d", interval="1m")
        if not df_oggi.empty:
            prezzo_attuale = df_oggi['Close'].iloc[-1]
            chiusura_ieri = t.info.get('previousClose', df_oggi['Close'].iloc)
            variazione = ((prezzo_attuale - chiusura_ieri) / chiusura_ieri) * 100
            return prezzo_attuale, variazione
        else:
            info = t.info
            p = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            v = info.get('regularMarketChangePercent', 0.0)
            if v and v > 0 and v < 1:  
                v = v * 100
            return p, v
    except:
        return 0.0, 0.0

def analizza_notizie_geopolitiche():
    """Scansiona i feed USA/Asia di Yahoo Finance alla ricerca di dazi, diciture geopolitiche o tensioni"""
    # Parole chiave per blocco semiconduttori / dazi USA-Asia
    parole_crisi_chips = [
        "tariff", "sanction", "export ban", "china", "taiwan", "restriction", 
        "trade war", "chips act", "white house", "biden", "trump", "beijing"
    ]
    # Parole chiave per spese militari / conflitti geopolitici
    parole_difesa = ["nato", "military", "defense", "pentagon", "spending", "missile", "war", "escalation"]
    
    score_chips = 0
    score_difesa = 0
    notizie_rilevate = []
    
    try:
        # Interroga i feed dei leader mondiali legati a USA e Asia
        for t_simbolo in ["TSM", "NVDA"]:
            ticker = yf.Ticker(t_simbolo)
            notizie = ticker.news
            if notizie:
                for n in notizie[:5]: # Controlla le 5 notizie più fresche
                    titolo = n.get('title', '').lower()
                    link = n.get('link', '#')
                    fonte = n.get('publisher', 'Yahoo Finance')
                    
                    # Rilevamento dazi o restrizioni economiche USA/Asia
                    if any(p in titolo for p in parole_crisi_chips):
                        score_chips -= 15
                        if n.get('title') not in notizie_rilevate:
                            notizie_rilevate.append({
                                "testo": f"⚠️ **{fonte}**: [{n.get('title')}]({link})",
                                "tipo": "chips"
                            })
                    
                    # Rilevamento tensioni militari o budget difesa
                    if any(p in titolo for p in parole_difesa):
                        score_difesa += 15
                        if n.get('title') not in notizie_rilevate:
                            notizie_rilevate.append({
                                "testo": f"🪖 **{fonte}**: [{n.get('title')}]({link})",
                                "tipo": "difesa"
                            })
    except:
        pass
        
    return score_chips, score_difesa, notizie_rilevate

# --- INTERFACCIA CRUSCOTTO ---
st.title("🤖 Real-Time Automated Chips & Geopolitical Monitor")

fuso_roma = pytz.timezone("Europe/Rome")
ora_esatta = datetime.now(fuso_roma).strftime("%H:%M:%S")
st.write(f"Ultimo aggiornamento automatico AI: **{ora_esatta}** (Sincronizzato Live)")

# ================= SIDEBAR: MONITOR NOTIZIE AUTOMATICO =================
peso_chips, peso_difesa, lista_notizie = analizza_notizie_geopolitiche()

st.sidebar.header("📰 Analizzatore Live USA & Asia")
st.sidebar.write("L'algoritmo scansiona i feed di Yahoo Finance alla ricerca di decisioni economiche e geopolitiche.")

if lista_notizie:
    # Sistema di Allerta Visiva in base al numero di notizie rilevate
    if len(lista_notizie) >= 3:
        st.sidebar.error("🚨 ALERT: Rilevato forte accumulo di notizie macroeconomiche/tensioni!")
    else:
        st.sidebar.warning("⚠️ ATTENZIONE: Rilevate notizie geopolitiche di rilievo.")
        
    st.sidebar.write("### Ultime notizie rilevate:")
    for noti in lista_notizie[:5]:
        st.sidebar.markdown(noti["testo"])
else:
    st.sidebar.success("🟢 Flussi geopolitici stabili. Nessun dazio o escalation rilevata nei feed attuali delle ultime ore.")

# ================= 1. I COLOSSI MONDIALI (USA & ASIA) =================
st.header("🇺🇸🌏 Driver Globali dei Semiconduttori")
st.write("Quotazioni in tempo reale dei leader di mercato che influenzano la borsa europea.")

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

# Calcolo e visualizzazione della spinta globale del comparto
indice_globale = (v_nvda + v_tsm + v_asml) / 3
st.info(f"📊 **Spinta Globale del Comparto:** In questo momento i colossi mondiali si muovono mediamente del **{indice_globale:.2f}%**.")

st.markdown("---")

# ================= 2. BORSA DI MILANO (CONSIGLI AUTOMATICI) =================
st.header("🇮🇹 Quotazioni Live Borsa di Milano")
st.write("Segnali automatici calcolati combinando l'andamento reale di Piazza Affari e i flussi informativi internazionali.")

col1, col2 = st.columns(2)

with col1:
    p_stm, v_stm = prendi_prezzo_live("STMMI.MI")
    st.subheader("STMicroelectronics (STM.MI)")
    st.metric(label="Prezzo Live Milano", value=f"€ {p_stm:.2f}", delta=f"{v_stm:.2f}%")
    
    # Calcolo Rating: Prezzo Milano + Trend USA/Asia + Peso Notizie dazi/sanzioni scansionate
    score_stm = v_stm + (indice_globale * 0.6) + peso_chips
    st.write(f"Rating di Flusso Automatizzato: **{score_stm:.2f}**")
    
    if score_stm < -5:
        st.error("🔴 EVITARE / VENDI: Forte pressione da dazi USA/Asia o crollo dei leader globali.")
    elif score_stm > 2.5:
        st.success("🟢 COMPRA: Ottima spinta dai colossi globali e zero tensioni commerciali rilevate.")
    else:
        st.warning("🟡 TIENI: Posizione di attesa. Il mercato sta assimilando i dati macroeconomici.")

with col2:
    p_ldo, v_ldo = prendi_prezzo_live("LDO.MI")
    st.subheader("Leonardo S.p.A. (LDO.MI)")
    st.metric(label="Prezzo Live Milano", value=f"€ {p_ldo:.2f}", delta=f"{v_ldo:.2f}%")
    
    # Calcolo Rating: Prezzo Milano + Peso Notizie spese militari/tensioni geopolitiche scansionate
    score_ldo = v_ldo + peso_difesa
    st.write(f"Rating di Flusso Automatizzato: **{score_ldo:.2f}**")
    
    if score_ldo > 8 or peso_difesa > 0:
        st.success("🟢 COMPRA: I feed rilevano un aumento globale delle spese militari o instabilità geopolitica.")
    elif score_ldo < -4:
        st.error("🔴 VENDI: Allentamento delle tensioni globali o prese di beneficio sul settore difesa.")
    else:
        st.warning("🟡 TIENI: Comparto stazionario. Il trend segue il normale andamento fisiologico di borsa.")
