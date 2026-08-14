def interroga_borsa_realtime(ticker_simbolo):
    """Interroga i server finanziari estraendo il prezzo istantaneo reale senza ritardo"""
    try:
        t = yf.Ticker(ticker_simbolo)
        
        # USARE FAST_INFO: Estrae il prezzo effettivo dell'ultimo secondo ignorando i 15 minuti di ritardo dei grafici
        prezzo_corrente = float(t.fast_info['last_price'])
        chiusura_precedente = float(t.fast_info['previous_close'])
        
        if prezzo_corrente > 0 and chiusura_precedente > 0:
            # Calcolo matematico immediato della variazione reale
            variazione_percentuale = ((prezzo_corrente - chiusura_precedente) / chiusura_precedente) * 100
            return prezzo_corrente, variazione_percentuale
            
    except Exception:
        # Sistema di backup se fast_info fallisce temporaneamente
        try:
            df_live = t.history(period="1d", interval="1m")
            df_ieri = t.history(period="2d", interval="1d")
            if not df_live.empty and len(df_ieri) >= 1:
                prezzo_corrente = float(df_live['Close'].iloc[-1])
                chiusura_precedente = float(df_ieri['Close'].iloc[-2]) if len(df_ieri) > 1 else float(df_ieri['Close'].iloc)
                variazione_percentuale = ((prezzo_corrente - chiusura_precedente) / chiusura_precedente) * 100
                return prezzo_corrente, variazione_percentuale
        except Exception:
            pass
            
    return 0.0, 0.0
