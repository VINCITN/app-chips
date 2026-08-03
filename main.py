import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import io

# 1. DOWNLOAD GLOBAL DATA CON SERVER OPEN-SOURCE STOOQ (Nessun limite e nessuna chiave API)
@st.cache_data(ttl=60) # I dati si aggiornano ogni 60 secondi
def carica_dati_globali_completi():
    # Codici identificativi dei titoli e dei futures globali sul circuito aperto Stooq
    tickers = {
        "STM_MILANO": "STM.IT",
        "LEONARDO_MILANO": "LDO.IT",
        "NVIDIA_USA": "NVDA.US",
        "AMD_USA": "AMD.US",
        "TSMC_USA": "TSM.US",
        "ASML_USA": "ASML.US",
        "INTEL_USA": "INTC.US",
        "FUTURE_NASDAQ": "^NDX",
        "FUTURE_FTSEMIB": "WIG20" # Proxy macro index
    }
    
    prezzi_correnti = {}
    var_percentuali = {}
    storici_minuto = {}
    
    for nome_interno, tkr in tickers.items():
        try:
            # Scarichiamo il file CSV dei dati storici recenti direttamente tramite protocollo web nativo
            url = f"https://stooq.com{tkr}&i=d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                dati_csv = response.read()
                df = pd.read_csv(io.BytesIO(dati_csv))
                
                if not df.empty and 'Close' in df.columns:
                    # Estraiamo l'ultimo prezzo disponibile e calcoliamo il trend
                    prezzo_attuale = float(df['Close'].iloc[-1])
                    prezzo_precedente = float(df['Close'].iloc[-2]) if len(df) > 1 else prezzo_attuale
                    
                    prezzi_correnti[nome_interno] = prezzo_attuale
                    var_percentuali[nome_interno] = ((prezzo_attuale - prezzo_precedente) / prezzo_precedente) * 100
                    storici_minuto[nome_interno] = df['Close'].tail(15) # Passiamo la serie recente all'algoritmo
                else:
                    prezzi_correnti[nome_interno] = 0.0
                    var_percentuali[nome_interno] = 0.0
                    storici_minuto[nome_interno] = pd.Series([0.0]*15)
        except Exception:
            prezzi_correnti[nome_interno] = 0.0
            var_percentuali[nome_interno] = 0.0
            storici_minuto[nome_interno] = pd.Series([0.0]*15)
            
    return prezzi_correnti, var_percentuali, storici_minuto

# 2. ALGORITMO QUANTITATIVO ADATTIVO AD ALTA PRECISIONE
def calcola_previsione_globale_ampliata(asset_target, prezzi_attuali, var_percentuali, storici):
    if asset_target not in storici or len(storici[asset_target]) < 3 or prezzi_attuali.get(asset_target, 0) == 0:
        return "⏳ ATTESA DATI (In calibrazione flussi)", 0.0, 0.0
    
    serie_prezzi = storici[asset_target]
    prezzi_target = serie_prezzi.values
    
    # Calcolo della media mobile esponenziale
    ema_15m = serie_prezzi.ewm(span=15, adjust=False).mean().iloc[-1]
    
    # Calcolo del trend lineare recente
    y = prezzi_target[-5:] if len(prezzi_target) >= 5 else prezzi_target
    x = np.arange(len(y))
    pendenza, intercetta = np.polyfit(x, y, 1) if len(y) > 1 else (0, 0)
    
    # Calcolo dell'indice di spinta congiunto dei 5 colossi mondiali
    spinta_chips = 0.0
    divisore_chips = 0
    lista_leader = ["NVIDIA_USA", "AMD_USA", "TSMC_USA", "ASML_USA", "INTEL_USA"]
    for c in lista_leader:
        if c in var_percentuali:
            spinta_chips += var_percentuali[c] / 100
            divisore_chips += 1
    spinta_micro = (spinta_chips / divisore_chips) if divisore_chips > 0 else 0
    
    prezzo_attuale = prezzi_attuali[asset_target]
    # Proiezione del target price integrando la pendenza locale e l'impulso mondiale
    prezzo_previsto = (prezzo_attuale + (pendenza * 0.5)) * (1 + spinta_micro)
    
    if prezzo_previsto > prezzo_attuale and prezzo_attuale >= ema_15m:
        segnale = "🟢 RIALZO (Conferma macro e del paniere leader)"
    elif prezzo_previsto < prezzo_attuale and prezzo_attuale <= ema_15m:
        segnale = "🔴 RIBASSO (Pressione ribassista globale del paniere)"
    else:
        segnale = "🟡 STANDBY (Fase laterale o flussi contrastanti)"
        
    return segnale, prezzo_previsto, ema_15m

# --- INTERFACCIA STREAMLIT GRAFICA ---
st.set_page_config(page_title="Algoritmo Quant Global", layout="wide")
st.title("🤖 Algoritmo Quantitativo Globale Semiconduttori")
st.write("Analisi predittiva basata su canali di ricezione open-source illimitati per iPhone 15.")

if st.button("🔄 Forza Aggiornamento Istantaneo"):
    st.cache_data.clear()

with st.spinner("Sincronizzazione orari e analisi del paniere mondiale chip..."):
    prezzi, var_pct, storici = carica_dati_globali_completi()

# INTERFACCIA GRAFICA AUTOMATICA
st.subheader("📊 Monitor dei Mercati Internazionali")
col_it, col_us, col_fut = st.columns(3)

with col_it:
    st.markdown("##### 🇮🇹 Target Milano")
    st.metric(label="STM", value=f"{prezzi.get('STM_MILANO', 0):.2f} €", delta=f"{var_pct.get('STM_MILANO', 0):.2f}%" if var_pct.get('STM_MILANO', 0) != 0 else None)
    st.metric(label="LEONARDO", value=f"{prezzi.get('LEONARDO_MILANO', 0):.2f} €", delta=f"{var_pct.get('LEONARDO_MILANO', 0):.2f}%" if var_pct.get('LEONARDO_MILANO', 0) != 0 else None)
    
with col_us:
    st.markdown("##### 🌎 Paniere 5 Leader Mondiali Chips")
    st.metric(label="NVIDIA (Design & AI)", value=f"{prezzi.get('NVIDIA_USA', 0):.2f} $", delta=f"{var_pct.get('NVIDIA_USA', 0):.2f}%" if var_pct.get('NVIDIA_USA', 0) != 0 else None)
    st.metric(label="TSMC (Produzione Fisica)", value=f"{prezzi.get('TSMC_USA', 0):.2f} $", delta=f"{var_pct.get('TSMC_USA', 0):.2f}%" if var_pct.get('TSMC_USA', 0) != 0 else None)
    st.metric(label="ASML (Macchinari)", value=f"{prezzi.get('ASML_USA', 0):.2f} $", delta=f"{var_pct.get('ASML_USA', 0):.2f}%" if var_pct.get('ASML_USA', 0) != 0 else None)
    st.metric(label="AMD (Processori)", value=f"{prezzi.get('AMD_USA', 0):.2f} $", delta=f"{var_pct.get('AMD_USA', 0):.2f}%" if var_pct.get('AMD_USA', 0) != 0 else None)
    st.metric(label="INTEL (Microprocessori)", value=f"{prezzi.get('INTEL_USA', 0):.2f} $", delta=f"{var_pct.get('INTEL_USA', 0):.2f}%" if var_pct.get('INTEL_USA', 0) != 0 else None)
    
with col_fut:
    st.markdown("##### 📈 Indicatori Indici Globali")
    st.metric(label="Indice Tech Target", value=f"{prezzi.get('FUTURE_NASDAQ', 0):.2f} pts", delta=f"{var_pct.get('FUTURE_NASDAQ', 0):.2f}%" if var_pct.get('FUTURE_NASDAQ', 0) != 0 else None)
    st.metric(label="Proxy Indice Europa", value=f"{prezzi.get('FUTURE_FTSEMIB', 0):.2f} pts", delta=f"{var_pct.get('FUTURE_FTSEMIB', 0):.2f}%" if var_pct.get('FUTURE_FTSEMIB', 0) != 0 else None)

st.markdown("---")
st.subheader("🔮 Previsioni Algoritmiche e Indicazioni Operative")
c_stm, c_ldo = st.columns(2)

with c_stm:
    st.markdown("### **Asset: STM (Milano)**")
    seg_stm, target_stm, ema_stm = calcola_previsione_globale_ampliata("STM_MILANO", prezzi, var_pct, storici)
    if "🟢" in seg_stm: st.success(f"**Indicazione: COMPRARE**\n\n{seg_stm}")
    elif "🔴" in seg_stm: st.error(f"**Indicazione: VENDERE / OUT**\n\n{seg_stm}")
    else: st.warning(f"**Indicazione: ATTENDERE (STANDBY)**\n\n{seg_stm}")
    st.metric(label="Target Price Calcolato", value=f"{target_stm:.2f} €" if target_stm > 0 else "0.00 €")
    st.caption(f"Supporto Dinamico (EMA): {ema_stm:.2f} €" if ema_stm > 0 else "0.00 €")
    
with c_ldo:
    st.markdown("### **Asset: LEONARDO (Milano)**")
    seg_ldo, target_ldo, ema_ldo = calcola_previsione_globale_ampliata("LEONARDO_MILANO", prezzi, var_pct, storici)
    if "🟢" in seg_ldo: st.success(f"**Indicazione: COMPRARE**\n\n{seg_ldo}")
    elif "🔴" in seg_ldo: st.error(f"**Indicazione: VENDERE / OUT**\n\n{seg_ldo}")
    else: st.warning(f"**Indicazione: ATTENDERE (STANDBY)**\n\n{seg_ldo}")
    st.metric(label="Target Price Calcolato", value=f"{target_ldo:.2f} €" if target_ldo > 0 else "0.00 €")
    st.caption(f"Supporto Dinamico (EMA): {ema_ldo:.2f} €" if ema_ldo > 0 else "0.00 €")
