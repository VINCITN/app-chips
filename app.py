import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. DOWNLOAD GLOBAL DATA (Paniere Ampliato + Pre/Post Market + Futures H24)
@st.cache_data(ttl=30) # Aggiornamento automatico ogni 30 secondi per massima reattività
def carica_dati_globali_completi():
    tickers = {
        # Azioni Target (Milano)
        "STM_MILANO": "STM.MI",
        "LEONARDO_MILANO": "LDO.MI",
        
        # PANIERE DEI 5 LEADER MONDIALI DEI CHIP (Incluso Pre/Post Market USA)
        "NVIDIA_USA": "NVDA",       # Leader AI e Capitalizzazione
        "AMD_USA": "AMD",           # Leader Processori e GPU
        "TSMC_USA": "TSM",          # Il più grande produttore fisico al mondo (Taiwan/USA)
        "ASML_USA": "ASML",         # Monopolio macchinari litografici avanzati (Olanda/USA)
        "INTEL_USA": "INTC",        # Gigante dei microprocessori integrati
        
        # Trend di Sfondo Internazionali (Futures attivi quasi 24h)
        "FUTURE_NASDAQ": "NQ=F",    # Futures NASDAQ 100
        "FUTURE_FTSEMIB": "STXE.MI" # Proxy macro per Europa/Milano
    }
    
    prezzi_correnti = {}
    var_percentuali = {}
    storici_minuto = {}
    
    for nome, ticker in tickers.items():
        ticker_obj = yf.Ticker(ticker)
        # Scarichiamo gli ultimi 3 giorni con candele a 1 minuto includendo i mercati estesi
        storico = ticker_obj.history(period="3d", interval="1m", prepost=True)
        
        if not storico.empty:
            storico_pulito = storico['Close'].dropna()
            if len(storico_pulito) > 1:
                prezzi_correnti[nome] = storico_pulito.iloc[-1]
                storici_minuto[nome] = storico_pulito
                
                # Calcolo della variazione percentuale giornaliera
                prezzo_apertura = storico['Open'].iloc[0]
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
            
    return prezzi_correnti, var_percentuali, storici_minuto

# 2. ALGORITMO QUANTITATIVO CON CORRELAZIONE FUTURES E PANIERE CHIPS
def calcola_previsione_globale_ampliata(asset_target, prezzi_attuali, var_percentuali, storici):
    if asset_target not in storici or len(storici[asset_target]) < 15:
        return "Calibrazione Dati...", 0.0, 0.0
    
    # Serie storica al minuto del titolo da prevedere
    serie_minuti = storici[asset_target]
    prezzi_target = serie_minuti.values
    
    # A. Media Mobile Esponenziale (EMA a 15 Minuti)
    ema_15m = serie_minuti.tail(15).ewm(span=15, adjust=False).mean().iloc[-1]
    
    # B. Regressione Lineare Rapida (Pendenza degli ultimi 15 minutes)
    y = prezzi_target[-15:]
    x = np.arange(len(y))
    pendenza, intercetta = np.polyfit(x, y, 1)
    
    # C. Calcolo dell'impulso dei Futures H24 (Sentiment macro-economico attuale)
    spinta_futures = 0.0
    divisore_futures = 0
    for f in ["FUTURE_NASDAQ", "FUTURE_FTSEMIB"]:
        if f in storici and len(storici[f]) >= 5:
            var_f = (storici[f].iloc[-1] - storici[f].iloc[-5]) / storici[f].iloc[-5]
            spinta_futures += var_f
            divisore_futures += 1
    spinta_macro = (spinta_futures / divisore_futures) if divisore_futures > 0 else 0
    
    # D. Calcolo dell'impulso del PANIERE ALLARGATO CHIPS (Ultimi 5 minuti)
    spinta_chips = 0.0
    divisore_chips = 0
    lista_leader = ["NVIDIA_USA", "AMD_USA", "TSMC_USA", "ASML_USA", "INTEL_USA"]
    
    for c in lista_leader:
        if c in storici and len(storici[c]) >= 5:
            var_c = (storici[c].iloc[-1] - storici[c].iloc[-5]) / storici[c].iloc[-5]
            spinta_chips += var_c
            divisore_chips += 1
    spinta_micro = (spinta_chips / divisore_chips) if divisore_chips > 0 else 0
    
    # E. Fusione Algoritmica (Trend Locale + Impulso Macro Futures + Impulso 5 Leader Mondiali)
    prezzo_attuale = prezzi_attuali[asset_target]
    prezzo_previsto = (prezzo_attuale + (pendenza * 5)) * (1 + spinta_macro + spinta_micro)
    
    # Generazione del segnale operativo ad incrocio protetto
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

if prezzi.get("STM_MILANO", 0) == 0:
    st.error("Errore di rete. Impossibile contattare i server finanziari mondiali. Riprova.")
else:
    # SEZIONE 1: VISUALIZZAZIONE DATI E PREZZI REAL-TIME CON VARIAZIONI %
    st.subheader("📊 Monitor dei Mercati Internazionali")
    
    col_it, col_us, col_fut = st.columns(3)
    
    with col_it:
        st.markdown("##### 🇮🇹 Target Milano")
        st.metric(label="STM", value=f"{prezzi['STM_MILANO']:.2f} €", delta=f"{var_pct['STM_MILANO']:.2f}%")
        st.metric(label="LEONARDO", value=f"{prezzi['LEONARDO_MILANO']:.2f} €", delta=f"{var_pct['LEONARDO_MILANO']:.2f}%")
        
    with col_us:
        st.markdown("##### 🌎 Paniere 5 Leader Mondiali Chips (Pre/Post USA)")
        st.metric(label="NVIDIA (Design & AI)", value=f"{prezzi['NVIDIA_USA']:.2f} $", delta=f"{var_pct['NVIDIA_USA']:.2f}%")
        st.metric(label="TSMC (Produzione Fisica)", value=f"{prezzi['TSMC_USA']:.2f} $", delta=f"{var_pct['TSMC_USA']:.2f}%")
        st.metric(label="ASML (Macchinari Litografici)", value=f"{prezzi['ASML_USA']:.2f} $", delta=f"{var_pct['ASML_USA']:.2f}%")
        st.metric(label="AMD (Processori & GPU)", value=f"{prezzi['AMD_USA']:.2f} $", delta=f"{var_pct['AMD_USA']:.2f}%")
        st.metric(label="INTEL (Microprocessori PC)", value=f"{prezzi['INTEL_USA']:.2f} $", delta=f"{var_pct['INTEL_USA']:.2f}%")
        
    with col_fut:
        st.markdown("##### 📈 Futures Macro & Indici (Sentiment H24)")
        st.metric(label="Futures NASDAQ 100", value=f"{prezzi['FUTURE_NASDAQ']:.2f} pts", delta=f"{var_pct['FUTURE_NASDAQ']:.2f}%")
        st.metric(label="Proxy Europa / Milano", value=f"{prezzi['FUTURE_FTSEMIB']:.2f} €", delta=f"{var_pct['FUTURE_FTSEMIB']:.2f}%")

    st.markdown("---")
    
    # SEZIONE 2: SEGNALI OPERATIVI GENERATI DALL'ALGORITMO
    st.subheader("🔮 Previsioni Algoritmiche e Indicazioni Operative")
    
    c_stm, c_ldo = st.columns(2)
    
    with c_stm:
        st.markdown("### **Asset: STM (Milano)**")
        seg_stm, target_stm, ema_stm = calcola_previsione_globale_ampliata("STM_MILANO", prezzi, var_pct, storici)
        
        # Gestione visiva intuitiva del segnale
        if "🟢" in seg_stm: st.success(f"**Indicazione: COMPRARE**\n\n{seg_stm}")
        elif "🔴" in seg_stm: st.error(f"**Indicazione: VENDERE / OUT**\n\n{seg_stm}")
        else: st.warning(f"**Indicazione: ATTENDERE (STANDBY)**\n\n{seg_stm}")
            
        st.metric(label="Target Price Calcolato (Prossimi Minuti)", value=f"{target_stm:.2f} €")
        st.caption(f"Supporto Dinamico (EMA 15m): {ema_stm:.2f} €")
        
    with col_ldo:
        st.markdown("### **Asset: LEONARDO (Milano)**")
        seg_ldo, target_ldo, ema_ldo = calcola_previsione_globale_ampliata("LEONARDO_MILANO", prezzi, var_pct, storici)
        
        if "🟢" in seg_ldo: st.success(f"**Indicazione: COMPRARE**\n\n{seg_ldo}")
        elif "🔴" in seg_ldo: st.error(f"**Indicazione: VENDERE / OUT**\n\n{seg_ldo}")
        else: st.warning(f"**Indicazione: ATTENDERE (STANDBY)**\n\n{seg_ldo}")
            
        st.metric(label="Target Price Calcolato (Prossimi Minuti)", value=f"{target_ldo:.2f} €")
        st.caption(f"Supporto Dinamico (EMA 15m): {ema_ldo:.2f} €")
