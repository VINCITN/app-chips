import asyncio
import threading
from datetime import datetime
from flask import Flask, render_template_string
import yfinance as yf

# --- CONFIGURAZIONE ---
TICKERS_CHIPS = {"NVDA": "NVIDIA", "TSM": "TSMC", "ASML": "ASML"}

# INDICI GEOPOLITICI (I nostri occhi sulle tensioni internazionali)
TICKERS_GEOPOLITICA = {
    "^VIX": "Indice Paura/Tensioni (VIX)",
    "ITA": "Fondo Difesa e Aerospazio Globale (iShares)",
}

TITOLI_MILANO = {"STM.MI": "STMicroelectronics", "LDO.MI": "Leonardo S.p.A."}

stato_mercato = {
    "chip_leaders": {},
    "geopolitica": {},
    "milano": {},
    "ultimo_aggiornamento": "Mai",
}

app = Flask(__name__)


# --- LOGICA DI CALCOLO ASINCRONA ---
async def monitoraggio_completo():
    print("[Sistema] Connessione continua mercati e geopolitica attiva...")
    while True:
        try:
            # 1. Analisi Semiconduttori (Come prima)
            chips_var, c_count = 0, 0
            for ticker in TICKERS_CHIPS.keys():
                t = yf.Ticker(ticker)
                df = t.history(period="1d", interval="1m")
                if not df.empty:
                    p_prec = t.info.get("previousClose", df["Close"].iloc[-1])
                    var = ((df["Close"].iloc[-1] - p_prec) / p_prec) * 100
                    chips_var += var
                    c_count += 1
            momentum_chips = chips_var / c_count if c_count > 0 else 0

            # 2. Analisi Geopolitica
            var_vix = 0.0  # Paura/Instabilità
            var_difesa = 0.0  # Spesa Militare Mondiale
            for ticker, nome in TICKERS_GEOPOLITICA.items():
                t = yf.Ticker(ticker)
                df = t.history(period="1d", interval="1m")
                if not df.empty:
                    p_prec = t.info.get("previousClose", df["Close"].iloc[-1])
                    var = ((df["Close"].iloc[-1] - p_prec) / p_prec) * 100
                    stato_mercato["geopolitica"][ticker] = {
                        "nome": nome,
                        "variazione": round(var, 2),
                    }
                    if ticker == "^VIX":
                        var_vix = var
                    elif ticker == "ITA":
                        var_difesa = var

            # 3. Calcolo Segnale per Milano con Matrice Geopolitica
            for ticker, nome in TITOLI_MILANO.items():
                t = yf.Ticker(ticker)
                df = t.history(period="1d", interval="1m")
                if not df.empty:
                    prezzo_live = df["Close"].iloc[-1]
                    # Chiediamo l'apertura per calcolare il trend giornaliero di Milano
                    df_day = t.history(period="1d")
                    var_milano = (
                        ((prezzo_live - df_day["Open"].iloc[-1]) / df_day["Open"].iloc[-1])
                        * 100
                    )

                    if "STM" in ticker:
                        # STM soffre se il VIX (paura/guerre commerciali) sale
                        # Ma beneficia dei chip globali
                        score = (
                            (var_milano * 0.5)
                            + (momentum_chips * 0.4)
                            - (var_vix * 0.1)
                        )
                        soglia_buy, soglia_sell = 0.4, -0.4
                    else:
                        # Leonardo beneficia direttamente se la Difesa Globale (ITA) sale
                        # E se il VIX (instabilità) aumenta l'allerta dei mercati
                        score = (
                            (var_milano * 0.5)
                            + (var_difesa * 0.3)
                            + (var_vix * 0.2)
                        )
                        soglia_buy, soglia_sell = 0.3, -0.3

                    # Verdetto finale
                    if score > soglia_buy:
                        decisione = "🔴 COMPRARE (BUY)"
                    elif score < soglia_sell:
                        decisione = "🟢 VENDERE (SELL)"
                    else:
                        decisione = "🟡 TENERE (HOLD)"

                    stato_mercato["milano"][ticker] = {
                        "nome": nome,
                        "prezzo": round(prezzo_live, 2),
                        "variazione": round(var_milano, 2),
                        "azione": decisione,
                    }

            stato_mercato["ultimo_aggiornamento"] = datetime.now().strftime(
                "%H:%M:%S"
            )
        except Exception as e:
            print(f"[Errore] Impossibile aggiornare: {e}")

        await asyncio.sleep(60)  # Interroga i mercati ogni minuto senza blocchi


def avvia_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(monitoraggio_completo())


# --- INTERFACCIA WEB ---
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Geopolitica e Chip</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: white; padding: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 8px; border-left: 6px solid #64748b; }
        .BUY { border-left-color: #ef4444; } .SELL { border-left-color: #22c55e; } .HOLD { border-left-color: #eab308; }
        h1, h2 { color: #38bdf8; }
        .badge { background: #334155; padding: 5px; border-radius: 4px; font-size: 0.9em; margin-right: 5px;}
    </style>
</head>
<body>
    <h1>Dashboard Decisionale Integrata (Geopolitica & Chip)</h1>
    <p>Ultimo controllo: <b>{{ dati['ultimo_aggiornamento'] }}</b></p>
    
    <h2>I Tuoi Titoli a Milano (Euro)</h2>
    <div class="grid">
        {% for ticker, info in dati['milano'].items() %}
            <div class="card {{ 'BUY' if 'COMPRARE' in info['azione'] else 'SELL' if 'VENDERE' in info['azione'] else 'HOLD' }}">
                <h3>{{ info['nome'] }} ({{ ticker }})</h3>
                <p>Prezzo Attuale: <b>{{ info['prezzo'] }} €</b> ({{ info['variazione'] }}%)</p>
                <p><b>SEGNALE ALGORITMO: {{ info['azione'] }}</b></p>
            </div>
        {% endfor %}
    </div>

    <h2>Indicatori di Rischio Geopolitico Internazionale</h2>
    <div class="grid">
        {% for ticker, info in dati['geopolitica'].items() %}
            <div class="card" style="border-left-color: #f43f5e;">
                <h4>{{ info['nome'] }}</h4>
                <p>Variazione Istantanea: <b>{{ info['variazione'] }}%</b></p>
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_DASHBOARD, dati=stato_mercato)


if __name__ == "__main__":
    threading.Thread(target=avvia_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
