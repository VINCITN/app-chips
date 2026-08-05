from datetime import datetime
import yfinance as yf

# --- CONFIGURAZIONE ASSET ---
# I tuoi titoli principali sulla Borsa di Milano (Prezzi in Euro)
TITOLI_MILANO = {
    "STM.MI": "STMicroelectronics",
    "LDO.MI": "Leonardo S.p.A."
}

# Leader mondiali dei chip (USA/Asia) per prevedere la crescita/perdita
TICKERS_CHIPS = {
    "NVDA": "NVIDIA (USA)",
    "TSM": "TSMC (Taiwan/USA)",
    "ASML": "ASML (Europa)"
}

# Indicatori Geopolitici Internazionali (Proxy di mercato)
TICKERS_GEOPOLITICA = {
    "^VIX": "Indice Incertezza/Tensioni (VIX)",
    "ITA": "Fondo Difesa Globale (iShares)"
}

def esegui_algoritmo_predittivo():
    print(f"=== ANALISI STRATEGICA INTEGRATA - {datetime.now().strftime('%H:%M:%S')} ===")
    print("Recupero dati di mercato globali in corso...\n")
    
    # 1. Calcolo dell'andamento dei Produttori Mondiali di Chip
    somma_var_chips = 0
    conteggio_chips = 0
    print("--- Comparto Chip Internazionale ---")
    for ticker, nome in TICKERS_CHIPS.items():
        try:
            t = yf.Ticker(ticker)
            df = t.history(period="1d", interval="1m")
            if not df.empty:
                chiusura_ieri = t.info.get("previousClose", df['Close'].iloc[-1])
                var_percentuale = ((df['Close'].iloc[-1] - chiusura_ieri) / chiusura_ieri) * 100
                somma_var_chips += var_percentuale
                conteggio_chips += 1
                print(f" > {nome}: {var_percentuale:+.2f}%")
        except Exception:
            continue
            
    momentum_chips_globale = somma_var_chips / conteggio_chips if conteggio_chips > 0 else 0
    print(f"-> Impulso Globale Semiconduttori: {momentum_chips_globale:+.2f}%\n")
    
    # 2. Analisi delle Tensioni Geopolitiche e Spesa Militare
    var_vix = 0.0      # Misura la paura/instabilità dei mercati
    var_difesa = 0.0   # Misura gli ordini del comparto difesa/aerospazio
    print("--- Scenario Geopolitico Internazionale ---")
    for ticker, nome in TICKERS_GEOPOLITICA.items():
        try:
            t = yf.Ticker(ticker)
            df = t.history(period="1d", interval="1m")
            if not df.empty:
                chiusura_ieri = t.info.get("previousClose", df['Close'].iloc[-1])
                var_percentuale = ((df['Close'].iloc[-1] - chiusura_ieri) / chiusura_ieri) * 100
                print(f" > {nome}: {var_percentuale:+.2f}%")
                if ticker == "^VIX":
                    var_vix = var_percentuale
                elif ticker == "ITA":
                    var_difesa = var_percentuale
        except Exception:
            continue
    print("")
    
    # 3. Elaborazione Segnale in Tempo Reale per la Borsa di Milano
    print("=== SEGNALI OPERATIVI PIAZZA AFFARI (VALUTA: EURO) ===")
    for ticker, nome in TITOLI_MILANO.items():
        try:
            t = yf.Ticker(ticker)
            # Forza l'intervallo a 1 minuto per aggirare il ritardo di 15 minuti delle API standard
            df = t.history(period="1d", interval="1m")
            
            if not df.empty:
                prezzo_in_euro = df['Close'].iloc[-1]
                df_giorno = t.history(period="1d")
                var_giornaliera_milano = ((prezzo_in_euro - df_giorno['Open'].iloc[-1]) / df_giorno['Open'].iloc[-1]) * 100
                
                # MATRICE DECISIONALE (Incrocio Chip + Geopolitica)
                if "STM" in ticker:
                    # STM beneficia dei chip globali ma soffre le guerre commerciali (VIX alto)
                    score_algoritmo = (var_giornaliera_milano * 0.5) + (momentum_chips_globale * 0.4) - (var_vix * 0.1)
                    soglia_buy, soglia_sell = 0.4, -0.4
                else:
                    # Leonardo beneficia se la difesa globale sale e se aumenta l'instabilità (VIX)
                    score_algoritmo = (var_giornaliera_milano * 0.5) + (var_difesa * 0.3) + (var_vix * 0.2)
                    soglia_buy, soglia_sell = 0.3, -0.3
                
                # Generazione Strategia
                if score_algoritmo > soglia_buy:
                    verdetto = "🔴 COMPRARE (BUY)"
                elif score_algoritmo < soglia_sell:
                    verdetto = "🟢 VENDERE (SELL)"
                else:
                    verdetto = "🟡 TENERE (HOLD)"
                    
                print(f"Titolo: {nome} ({ticker})")
                print(f" > Prezzo Live: {prezzo_in_euro:.2f} € ({var_giornaliera_milano:+.2f}%)")
                print(f" > Score di Valutazione: {score_algoritmo:+.2f}")
                print(f" > AZIONE CONSIGLIATA: {verdetto}\n")
        except Exception as e:
            print(f"Impossibile analizzare {nome}: {e}")

if __name__ == "__main__":
    esegui_algoritmo_predittivo()
