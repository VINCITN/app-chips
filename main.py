import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. DOWNLOAD GLOBAL DATA CON RECUPERO STORICO REALE A 5 GIORNI
@st.cache_data(ttl=30) # Cache rapida a 30 secondi
def carica_dati_globali_completi():
    tickers = {
        "STM_MILANO": "STM.MI",
        "LEONARDO_MILANO": "LDO.MI",
        "NVIDIA_USA": "NVDA",
        "AMD_USA": "AMD",
        "TSMC_USA": "TSM",
        "ASML_USA": "ASML",
        "INTEL_USA": "INTC",
        "FUTURE_NASDAQ": "NQ=F",
        "FUTURE_FTSEMIB": "STXE.MI"
    }
    
    prezzi_correnti = {}
    var_percentuali = {}
    storici_minuto = {}
    
    yf.set_tz_cache_location(None) # Evita i blocchi di fuso orario su Streamlit
    
    for nome, ticker in tickers.items():
        try:
            ticker_obj = yf.Ticker(ticker)
            # USIAMO "5d" AL POSTO DI "1d" per evitare tabelle vuote a borsa chiusa o nel weekend
            storico = ticker_obj.history(period="5d", interval="1m", prepost=True)
            
            if not storico.empty:
                storico_pulito = storico['Close'].dropna()
                if len(storico_pulito) > 1:
                    prezzi_correnti[nome] = storico_pulito.iloc[-1]
                    storici_minuto[nome] = storico_pulito
                    
                    # Calcolo della variazione percentuale prendendo l'apertura effettiva del set dati
                    prezzo_apertura = storico['Open'].dropna().iloc[0] if len(storico['Open'].dropna()) > 0 else storico_pulito.iloc[-1]
                    if prezzo_apertura > 0:
                        var_percentuali[nome] = ((storico_pulito.iloc[-1] - prezzo_apertura) / prezzo_apertura) * 100
                    else:
                        var_percentuali[nome] = 0.0
                else:
                    prezzi_correnti[nome] = storico_pulito.iloc[-1] if len(storico_pulito) == 1 else 0.0
                    var_percentuali[nome] = 0.0
            else:
                prezzi_correnti[nome] = 0.0
                var_percentuali[nome] = 0.0
        except Exception:
            prezzi_correnti[nome] = 0.0
            var_percentuali[nome] = 0.0
            
    return prezzi_correnti, var_percentuali, storici_minuto

# 2. ALGORITMO QUANTITATIVO ADATTIVO (Funziona sempre)
def calcola_previsione_globale_ampliata(asset_target, prezzi_attuali, var_percentuali, storici):
    if asset_target not in storici or len(storici[asset_target]) < 5 or prezzi_attuali.get(asset_target, 0) == 0:
        return "⏳ CALIBRAZIONE (In attesa di flussi)", 0.0, 0.0
    
    serie_minuti = storici[asset_target]
    prezzi_target = serie_minuti.values
    
    # Calcolo indicatori sulle candele disponibili
    ema_15m = serie_minuti.tail(15).ewm(span=15, adjust=False).mean().iloc[-1] if len(serie_minuti) >= 15 else prezzi_target[-1]
    
    y = prezzi_target[-15:] if len(prezzi_target) >= 15 else prezzi_target
    x = np.arange(len(y))
    pendenza, intercetta = np.polyfit(x, y, 1) if len(y) > 1 else (0, 0)
    
    # Impulso Futures (Ultimi minuti disponibili)
    spinta_futures = 0.0
    divisore_futures = 0
    for f in ["FUTURE_NASDAQ", "FUTURE_FTSEMIB"]:
        if f in storici and len(storici[f]) >= 5:
            var_f = (storici[f].iloc[-1] - storici[f].iloc[-5]) / storici[f].iloc[-5]
            spinta_futures += var_f
            divisore_futures += 1
    spinta_macro = (spinta_futures / divisore_futures) if divisore_futures > 0 else 0
    
    # Impulso Basket Semiconduttori Globali
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
    prezzo_previsto = (prezzo_attuale + (pendenza * 5)) * (1 + spinta_macro + spinta_micro)
    
    if prezzo_previsto > prezzo_attuale and prezzo_attuale > ema_15m and pendenza > 0:
        segnale = "🟢 RIALZO (Conferma macro e del paniere leader)"
    elif prezzo_previsto < prezzo_attuale and prezzo_attuale < ema_15m and pendenza < 0:
        segnale = "🔴 RIBASSO (Pressione ribassista globale del paniere)"
    else:
        segnale = "🟡 STANDBY (Fase laterale o flussi contrastanti USA/Milano)"
        
    return segnale, prezzo_previsto, ema_15m

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Algoritmo Quant Global", layout="wide")
st.title("🤖 Algoritmo Quantitativo Globale Semiconduttori")
st.write("Analisi predittiva al minuto basata sulle interconnessioni di Piazza Affari con i 5 leader mondiali dei chip e i Futures H24.")

if st.button("🔄 Forza Aggiornamento Istantaneo"):
    st.cache_data.clear()

with st.spinner("Sincronizzazione orari e analisi del paniere mondiale chip..."):
    prezzi, var_pct, storici = carica_dati_globali_completi()

# INTERFACCIA GRAFICA AUTOMATICA
st.subheader("📊 Monitor dei Mercati Internazionali")
col_it, col_us, col_fut = st.columns(3)

with col_it:
    st.markdown("##### 🇮🇹 Target Milano")
    st.metric(label="STM", value=f"{prezzi.get('STM_MILANO', 0):.2f} €", delta=f"{var_pct.get('STM_MILANO', 0):.2f}%")
    st.metric(label="LEONARDO", value=f"{prezzi.get('LEONARDO_MILANO', 0):.2f} €", delta=f"{var_pct.get('LEONARDO_MILANO', 0):.2f}%")
    
with col_us:
    st.markdown("##### 🌎 Paniere 5 Leader Mondiali Chips (Pre/Post USA)")
    st.metric(label="NVIDIA (Design & AI)", value=f"{prezzi.get('NVIDIA_USA', 0):.2f} $", delta=f"{var_pct.get('NVIDIA_USA', 0):.2f}%")
    st.metric(label="TSMC (Produzione Fisica)", value=f"{prezzi.get('TSMC_USA', 0):.2f} $", delta=f"{var_pct.get('TSMC_USA', 0):.2f}%")
    st.metric(label="ASML (Macchinari)", value=f"{prezzi.get('ASML_USA', 0):.2f} $", delta=f"{var_pct.get('ASML_USA', 0):.2f}%")
    st.metric(label="AMD (Processori)", value=f"{prezzi.get('AMD_USA', 0):.2f} $", delta=f"{var_pct.get('AMD_USA', 0):.2f}%")
    st.metric(label="INTEL (Microprocessori)", value=f"{prezzi.get('INTEL_USA', 0):.2f} $", delta=f"{var_pct.get('INTEL_USA', 0):.2f}%")
    
with col_fut:
    st.markdown("##### 📈 Futures Macro & Indici (Sentiment H24)")
    st.metric(label="Futures NASDAQ 100", value=f"{prezzi.get('FUTURE_NASDAQ', 0):.2f} pts", delta=f"{var_pct.get('FUTURE_NASDAQ', 0):.2f}%")
    st.metric(label="Proxy Europa / Milano", value=f"{prezzi.get('FUTURE_FTSEMIB', 0):.2f} €", delta=f"{var_pct.get('FUTURE_FTSEMIB', 0):.2f}%")

st.markdown("---")
st.subheader("🔮 Previsioni Algoritmiche e Indicazioni Operative")
c_stm, c_ldo = st.columns(2)

with c_stm:
    st.markdown("### **Asset: STM (Milano)**")
    seg_stm, target_stm, ema_stm = calcola_previsione_globale_ampliata("STM_MILANO", prezzi, var_pct, storici)
    if "🟢" in seg_stm: st.success(f"**Indicazione: COMPRARE**\n\n{seg_stm}")
    elif "🔴" in seg_stm: st.error(f"**Indicazione: VENDERE / OUT**\n\n{seg_stm}")
    else: st.warning(f"**Indicazione: ATTENDERE (STANDBY)**\n\n{seg_stm}")
    st.metric(label="Target Price Calcolato", value=f"{target_stm:.2f} €")
    st.caption(f"Supporto Dinamico (EMA): {ema_stm:.2f} €")
    
with c_ldo:
    st.markdown("### **Asset: LEONARDO (Milano)**")
    seg_ldo, target_ldo, ema_ldo = calcola_previsione_globale_ampliata("LEONARDO_MILANO", prezzi, var_pct, storici)
    if "🟢" in seg_ldo: st.success(f"**Indicazione: COMPRARE**\n\n{seg_ldo}")
    elif "🔴" in seg_ldo: st.error(f"**Indicazione: VENDERE / OUT**\n\n{seg_ldo}")
    else: st.warning(f"**Indicazione: ATTENDERE (STANDBY)**\n\n{seg_ldo}")
    st.metric(label="Target Price Calcolato", value=f"{target_ldo:.2f} €")
    st.caption(f"Supporto Dinamico (EMA): {ema_ldo:.2f} €")
