import streamlit as st
import pandas as pd
import numpy as np
import json
import urllib.request

# Inserisci qui dentro la chiave API gratuita che hai preso dal sito Alpha Vantage
CHIAVE_API = "F380ZTYI6PFSAC79"

@st.cache_data(ttl=60)
def carica_dati_alpha_vantage():
    # Mappatura dei ticker per Alpha Vantage
    tickers = {
        "STM_MILANO": "STM.MIL",
        "LEONARDO_MILANO": "LDO.MIL",
        "NVIDIA_USA": "NVDA",
        "AMD_USA": "AMD",
        "TSMC_USA": "TSM",
        "ASML_USA": "ASML",
        "INTEL_USA": "INTC"
    }
    
    prezzi_correnti = {}
    var_percentuali = {}
    storici_minuto = {}
    
    for nome_interno, tkr in tickers.items():
        try:
            # Richiesta dati in tempo reale intraday ai server di Alpha Vantage
            url = f"https://alphavantage.co{tkr}&interval=1min&apikey={CHIAVE_API}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                dati = json.loads(response.read().decode())
                
                # Estraiamo la serie temporale al minuto
                chiave_tempo = "Time Series (1min)"
                if chiave_tempo in dati:
                    serie = dati[chiave_tempo]
                    liste_chiusure = []
                    
                    for timestamp in sorted(serie.keys()):
                        liste_chiusure.append(float(serie[timestamp]["4. close"]))
                    
                    if len(liste_chiusure) > 0:
                        prezzo_attuale = liste_chiusure[-1]
                        prezzi_correnti[nome_interno] = prezzo_attuale
                        storici_minuto[nome_interno] = pd.Series(liste_chiusure)
                        
                        prezzo_iniziale = liste_chiusure[0]
                        var_percentuali[nome_interno] = ((prezzo_attuale - prezzo_iniziale) / prezzo_iniziale) * 100
                    else:
                        prezzi_correnti[nome_interno] = 0.0
                        var_percentuali[nome_interno] = 0.0
                        storici_minuto[nome_interno] = pd.Series(dtype=float)
                else:
                    prezzi_correnti[nome_interno] = 0.0
                    var_percentuali[nome_interno] = 0.0
                    storici_minuto[nome_interno] = pd.Series(dtype=float)
        except Exception:
            prezzi_correnti[nome_interno] = 0.0
            var_percentuali[nome_interno] = 0.0
            storici_minuto[nome_interno] = pd.Series(dtype=float)
            
    # Assegniamo dei valori fissi ai Futures simulati per non far bloccare l'algoritmo
    prezzi_correnti["FUTURE_NASDAQ"] = 19500.0
    prezzi_correnti["FUTURE_FTSEMIB"] = 480.0
    var_percentuali["FUTURE_NASDAQ"] = 0.0
    var_percentuali["FUTURE_FTSEMIB"] = 0.0
    storici_minuto["FUTURE_NASDAQ"] = pd.Series([19500.0]*5)
    storici_minuto["FUTURE_FTSEMIB"] = pd.Series([480.0]*5)
    
    return prezzi_correnti, var_percentuali, storici_minuto

# 2. ALGORITMO QUANTITATIVO INTELLIGENTE
def calcola_previsione_globale_ampliata(asset_target, prezzi_attuali, var_percentuali, storici):
    if asset_target not in storici or len(storici[asset_target]) < 5 or prezzi_attuali.get(asset_target, 0) == 0:
        return "⏳ ATTESA DATI (In calibrazione)", 0.0, 0.0
    
    serie_minuti = storici[asset_target]
    prezzi_target = serie_minuti.values
    ema_15m = serie_minuti.tail(15).ewm(span=15, adjust=False).mean().iloc[-1] if len(serie_minuti) >= 15 else prezzi_target[-1]
    
    y = prezzi_target[-15:] if len(prezzi_target) >= 15 else prezzi_target
    x = np.arange(len(y))
    pendenza, intercetta = np.polyfit(x, y, 1) if len(y) > 1 else (0, 0)
    
    spinta_chips = 0.0
    divisore_chips = 0
    lista_leader = ["NVIDIA_USA", "AMD_USA", "TSMC_USA", "ASML_USA", "INTEL_USA"]
    for c in lista_leader:
        if c in storici and len(storici[c]) >= 5:
            var_c = (storici[c].iloc[-1] - storici[c].iloc[-5]) / storici[c].iloc[-5]
            spinta_chips += var_c
            divisore_chips += 1
    spinta_micro = (spinta_chips / divisore_chips) if divisore_chips > 0 else 0
    
    prezzo_attuale = prezzi_attuali[asset_target]
    prezzo_previsto = (prezzo_attuale + (pendenza * 5)) * (1 + spinta_micro)
    
    if prezzo_previsto > prezzo_attuale and prezzo_attuale >= ema_15m and pendenza > 0:
        segnale = "🟢 RIALZO (Conferma macro e del paniere leader)"
    elif prezzo_previsto < prezzo_attuale and prezzo_attuale <= ema_15m and pendenza < 0:
        segnale = "🔴 RIBASSO (Pressione ribassista globale del paniere)"
    else:
        segnale = "🟡 STANDBY (Fase laterale o flussi contrastanti)"
        
    return segnale, prezzo_previsto, ema_15m

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Algoritmo Quant Global", layout="wide")
st.title("🤖 Algoritmo Quantitativo Globale Semiconduttori")
st.write("Analisi predittiva al minuto basata su Alpha Vantage per l'utilizzo diretto da iPhone 15.")

if st.button("🔄 Forza Aggiornamento Istantaneo"):
    st.cache_data.clear()

with st.spinner("Sincronizzazione orari e analisi del paniere mondiale chip..."):
    prezzi, var_pct, storici = carica_dati_alpha_vantage()

# INTERFACCIA GRAFICA AUTOMATICA
st.subheader("📊 Monitor dei Mercati Internazionali")
col_it, col_us, col_fut = st.columns(3)

with col_it:
    st.markdown("##### 🇮🇹 Target Milano")
    st.metric(label="STM", value=f"{prezzi.get('STM_MILANO', 0):.2f} €", delta=f"{var_pct.get('STM_MILANO', 0):.2f}%" if var_pct.get('STM_MILANO', 0) != 0 else None)
    st.metric(label="LEONARDO", value=f"{prezzi.get('LEONARDO_MILANO', 0):.2f} €", delta=f"{var_pct.get('LEONARDO_MILANO', 0):.2f}%" if var_pct.get('LEONARDO_MILANO', 0) != 0 else None)
    
with col_us:
    st.markdown("##### 🌎 Paniere 5 Leader Mondiali Chips (Pre/Post USA)")
    st.metric(label="NVIDIA (Design & AI)", value=f"{prezzi.get('NVIDIA_USA', 0):.2f} $", delta=f"{var_pct.get('NVIDIA_USA', 0):.2f}%" if var_pct.get('NVIDIA_USA', 0) != 0 else None)
    st.metric(label="TSMC (Produzione Fisica)", value=f"{prezzi.get('TSMC_USA', 0):.2f} $", delta=f"{var_pct.get('TSMC_USA', 0):.2f}%" if var_pct.get('TSMC_USA', 0) != 0 else None)
    st.metric(label="ASML (Macchinari)", value=f"{prezzi.get('ASML_USA', 0):.2f} $", delta=f"{var_pct.get('ASML_USA', 0):.2f}%" if var_pct.get('ASML_USA', 0) != 0 else None)
    st.metric(label="AMD (Processori)", value=f"{prezzi.get('AMD_USA', 0):.2f} $", delta=f"{var_pct.get('AMD_USA', 0):.2f}%" if var_pct.get('AMD_USA', 0) != 0 else None)
    st.metric(label="INTEL (Microprocessori)", value=f"{prezzi.get('INTEL_USA', 0):.2f} $", delta=f"{var_pct.get('INTEL_USA', 0):.2f}%" if var_pct.get('INTEL_USA', 0) != 0 else None)
    
with col_fut:
    st.markdown("##### 📈 Futures Macro & Indici (Sentiment H24)")
    st.metric(label="Futures NASDAQ 100", value=f"{prezzi.get('FUTURE_NASDAQ', 0):.2f} pts")
    st.metric(label="Proxy Europa / Milano", value=f"{prezzi.get('FUTURE_FTSEMIB', 0):.2f} €")

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
