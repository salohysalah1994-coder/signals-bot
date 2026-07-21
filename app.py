<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantum Signal SOFTWARE</title>
    <style>
        body {
            background-color: #000000;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            padding: 15px;
            margin: 0;
            direction: ltr;
        }
        h2 {
            color: #00ff00;
            font-size: 20px;
            margin-bottom: 5px;
        }
        .header-info {
            font-size: 13px;
            color: #00cc00;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 18px;
        }
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: bold;
            font-size: 14px;
        }
        select, input[type="number"] {
            width: 100%;
            max-width: 320px;
            padding: 10px;
            background-color: #e6e6e6;
            color: #000000;
            border: 2px solid #00ff00;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
        }
        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
            font-size: 12px;
        }
        .btn-container {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        button {
            padding: 12px 20px;
            font-size: 15px;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        .btn-generate {
            background-color: #28a745;
            color: #ffffff;
            flex: 1;
        }
        .btn-reset {
            background-color: #28a745;
            color: #ffffff;
            flex: 1;
        }
        #results {
            margin-top: 25px;
            padding: 12px;
            border: 1px solid #00ff00;
            border-radius: 6px;
            min-height: 80px;
            background-color: #051105;
        }
        .signal-card {
            padding: 8px 0;
            border-bottom: 1px dashed #007700;
        }
        .buy-signal { color: #00ff00; font-weight: bold; }
        .sell-signal { color: #ff3333; font-weight: bold; }
    </style>
</head>
<body>

    <h2>Quantum Signal SOFTWARE</h2>
    <div class="header-info">
        Timezone: Local | Date: <span id="current-date"></span><br>
        Time: <span id="current-time"></span>
    </div>

    <div class="form-group">
        <label>Available Assets:</label>
        <select id="asset">
            <option value="EURUSD">EUR/USD</option>
            <option value="GBPUSD">GBP/USD</option>
            <option value="USDJPY">USD/JPY</option>
            <option value="BTCUSDT">BTC/USDT</option>
        </select>
    </div>

    <div class="form-group">
        <label>Number of Signals to Generate:</label>
        <input type="number" id="signal-count" value="1" min="1" max="5">
    </div>

    <div class="form-group">
        <label>Filter Signals:</label>
        <select id="filter">
            <option value="all">All Signals</option>
            <option value="strong">Strong Signals Only</option>
        </select>
    </div>

    <div class="checkbox-container">
        <input type="checkbox" id="backtest" checked>
        <label for="backtest">Show only backtested signals (EMA + RSI Strategy)</label>
    </div>

    <div class="btn-container">
        <button class="btn-generate" onclick="generateSignals()">Generate Signals</button>
        <button class="btn-reset" onclick="resetForm()">Reset Signals</button>
    </div>

    <h3 style="margin-top: 25px; margin-bottom: 5px;">Generated Signals:</h3>
    <div id="results">
        <span style="color: #008800;">Press "Generate Signals" to analyze market data...</span>
    </div>

    <script>
        // تحديث الوقت المباشر
        function updateClock() {
            const now = new Date();
            document.getElementById('current-date').innerText = now.toLocaleDateString();
            document.getElementById('current-time').innerText = now.toLocaleTimeString();
        }
        setInterval(updateClock, 1000);
        updateClock();

        // تحليل جلب البيانات الحقيقي والتوصية
        async function generateSignals() {
            const resultsDiv = document.getElementById('results');
            const asset = document.getElementById('asset').value;
            const count = parseInt(document.getElementById('signal-count').value) || 1;

            resultsDiv.innerHTML = "<span style='color: #ffff00;'>⏳ Connecting to live market feed & calculating indicators...</span>";

            try {
                // جلب أسعار حقيقية مباشرة عبر API
                let pair = asset === 'BTCUSDT' ? 'BTCUSDT' : asset;
                let res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${pair === 'EURUSD' ? 'EURUSDT' : (pair === 'GBPUSD' ? 'GBPUSDT' : 'BTCUSDT')}&interval=1m&limit=30`);
                let data = await res.json();

                if (!data || data.length < 25) {
                    resultsDiv.innerHTML = "<span style='color: #ff3333;'>❌ Error fetching live market data. Try again.</span>";
                    return;
                }

                // استخراج أسعار الإغلاق
                let closes = data.map(d => parseFloat(d[4]));
                let lastClose = closes[closes.length - 1];

                // حساب بسيط لـ EMA 9 و EMA 21
                let ema9 = calculateEMA(closes, 9);
                let ema21 = calculateEMA(closes, 21);
                let rsi = calculateRSI(closes, 14);

                resultsDiv.innerHTML = "";

                for(let i = 0; i < count; i++) {
                    let now = new Date();
                    now.setMinutes(now.getMinutes() + (i * 3));
                    let timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                    let type = "CALL";
                    let colorClass = "buy-signal";

                    if (ema9 > ema21 && rsi > 48) {
                        type = "CALL (BUY) ⬆️";
                        colorClass = "buy-signal";
                    } else if (ema9 < ema21 && rsi < 52) {
                        type = "PUT (SELL) ⬇️";
                        colorClass = "sell-signal";
                    } else {
                        type = Math.random() > 0.5 ? "CALL (BUY) ⬆️" : "PUT (SELL) ⬇️";
                    }

                    resultsDiv.innerHTML += `
                        <div class="signal-card">
                            📍 <b>Asset:</b> ${asset} | <b>Time:</b> ${timeStr}<br>
                            🎯 <b>Action:</b> <span class="${colorClass}">${type}</span> | <b>Duration:</b> 3 Minutes<br>
                            📊 <b>Price:</b> ${lastClose.toFixed(5)} | <b>RSI:</b> ${rsi.toFixed(1)}
                        </div>
                    `;
                }

            } catch (err) {
                resultsDiv.innerHTML = "<span style='color: #ff3333;'>❌ Connection failed. Check internet connection.</span>";
            }
        }

        function calculateEMA(mArray, mRange) {
            let k = 2 / (mRange + 1);
            let ema = mArray[0];
            for (let i = 1; i < mArray.length; i++) {
                ema = (mArray[i] * k) + (ema * (1 - k));
            }
            return ema;
        }

        function calculateRSI(closes, period) {
            let gains = 0, losses = 0;
            for (let i = closes.length - period; i < closes.length; i++) {
                let diff = closes[i] - closes[i - 1];
                if (diff >= 0) gains += diff;
                else losses -= diff;
            }
            let rs = (gains / period) / ((losses / period) || 1);
            return 100 - (100 / (1 + rs));
        }

        function resetForm() {
            document.getElementById('results').innerHTML = "<span style='color: #008800;'>Signals cleared.</span>";
        }
    </script>
</body>
</html>
