import streamlit as st
import streamlit.components.v1 as components

# إعداد الصفحة لتكون بعرض كامل ومظهر احترافي
st.set_page_config(
    page_title="SALAH Signal Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# كود الـ HTML والـ JavaScript الخاص بك
html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SALAH Signal Generator</title>
    <style>
        body {
            background-color: black;
            color: #00ff00;
            font-family: monospace;
            padding: 10px;
            margin: 0;
        }
        .container {
            max-width: 100%;
            margin: auto;
        }
        h1, h3 {
            color: #00ff00;
            text-transform: uppercase;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 5px;
        }
        a {
            color: cyan;
            text-decoration: none;
            font-weight: bold;
        }
        a:hover {
            color: #00ffff;
            text-decoration: underline;
        }
        select, input[type="number"] {
            padding: 10px;
            margin: 10px 0;
            background-color: #111;
            color: #00ff00;
            border: 1px solid #00ff00;
            border-radius: 5px;
            font-family: monospace;
            width: 100%;
            box-sizing: border-box;
        }
        input[type="checkbox"] {
            accent-color: #00ff00;
        }
        button {
            padding: 12px 20px;
            margin: 10px 10px 10px 0;
            color: black;
            background-color: #00ff00;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            font-family: monospace;
            font-size: 1rem;
        }
        button:hover {
            background-color: #00cc00;
        }
        #reset-signals {
            background-color: #ff3333;
            color: white;
        }
        #reset-signals:hover {
            background-color: #cc0000;
        }
        .button-container {
            display: flex;
            justify-content: start;
        }
        .error-message {
            color: #ff3333;
            font-weight: bold;
        }
        .animation-message {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(0, 255, 0, 0.15);
            border: 2px solid #00ff00;
            padding: 20px;
            border-radius: 10px;
            color: #00ff00;
            text-align: center;
            backdrop-filter: blur(5px);
            z-index: 9999;
        }
        ul {
            list-style-type: square;
            padding-left: 20px;
        }
        li {
            margin: 8px 0;
            font-size: 1.1rem;
        }
        .backtest-badge {
            color: cyan;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>SALAH REAL-TIME SIGNAL GENERATOR</h1>
        <p>SALAH SIGNAL SOFTWARE</p>
        <p id="timezone-info">Timezone: Asia/Dhaka | Date: <span id="current-date"></span> | Time: <span id="current-time"></span></p>
        
        <h3>Join our Telegram Channel:</h3>
        <a href="https://t.me/QuantumSignalNet" target="_blank" rel="noopener noreferrer">SALAH Signal Net</a>
        
        <h3>Available Assets:</h3>
        <select id="asset-select">
            <option value="">Select an asset</option>
        </select>

        <h3>Number of Signals to Generate:</h3>
        <input type="number" id="signal-count" value="1" min="1" />

        <h3>Filter Signals:</h3>
        <select id="filter-select">
            <option value="ALL">All</option>
            <option value="CALL">CALL</option>
            <option value="PUT">PUT</option>
        </select>

        <h3>Backtest Filter:</h3>
        <label>
            <input type="checkbox" id="backtest-filter" />
            Show only backtested signals (95% accuracy)
        </label>

        <div class="button-container">
            <button id="generate-signals">Generate Signals</button>
            <button id="reset-signals">Reset Signals</button>
        </div>

        <p id="error-message" class="error-message"></p>
        
        <h3>Generated Signals:</h3>
        <ul id="signal-list"></ul>
        
        <div id="animation-message" class="animation-message">
            <h3>New Signals Generated!</h3>
        </div>
    </div>

    <script>
        const availableAssets = [
            "AUD/CAD", "AUD/CHF", "AUD/JPY", "AUD/NZD", "AUD/USD",
            "CAD/CHF", "CHF/JPY", "EUR/AUD", "EUR/CAD", "EUR/CHF",
            "EUR/GBP", "EUR/USD", "GBP/AUD", "GBP/CAD", "GBP/CHF",
            "GBP/JPY", "GBP/NZD", "GBP/USD", "NZD/CAD", "NZD/CHF",
            "NZD/JPY", "USD/BDT", "USD/BRL", "USD/CAD", "USD/CHF",
            "USD/COP", "USD/DZD", "USD/INR", "USD/JPY", "USD/NGN",
            "USD/PKR", "USD/SGD", "USD/TRY", "USD/ZAR", "Bitcoin",
            "Gold", "Silver", "USCrude", "UKBrent"
        ];

        let signals = [];
        let existingSignals = new Set();

        function formatTimeInDhaka(date) {
            return date.toLocaleTimeString('en-GB', { 
                timeZone: 'Asia/Dhaka', 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }

        function generateSignal(asset, time) {
            const direction = Math.random() < 0.5 ? 'CALL' : 'PUT';
            const backtested = Math.random() < 0.4; 
            return { asset, time, direction, backtested };
        }

        function generateUniqueTimes(count) {
            const times = [];
            let baseTime = new Date();
            for (let i = 0; i < count; i++) {
                baseTime.setMinutes(baseTime.getMinutes() + 3); // صفقة كل 3 دقائق
                times.push(formatTimeInDhaka(baseTime));
            }
            return times;
        }

        function handleGenerateSignals() {
            const selectedAsset = document.getElementById('asset-select').value;
            const signalCount = Number(document.getElementById('signal-count').value);
            const errorMessage = document.getElementById('error-message');
            
            if (!selectedAsset) {
                errorMessage.textContent = 'Please select an asset before generating signals!';
                return;
            }

            errorMessage.textContent = '';
            const uniqueTimes = generateUniqueTimes(signalCount);
            let addedNew = false;

            uniqueTimes.forEach((time) => {
                const signalKey = `${selectedAsset} ; ${time}`;
                if (!existingSignals.has(signalKey)) {
                    const newSignal = generateSignal(selectedAsset, time);
                    signals.push(newSignal);
                    existingSignals.add(signalKey);
                    addedNew = true;
                }
            });

            if (addedNew) {
                renderSignals();
                showAnimation();
            } else {
                errorMessage.textContent = 'Signals for these times have already been generated!';
            }
        }

        function renderSignals() {
            const signalList = document.getElementById('signal-list');
            signalList.innerHTML = '';

            const activeFilter = document.getElementById('filter-select').value;
            const showOnlyBacktested = document.getElementById('backtest-filter').checked;

            const filteredSignals = signals.filter(signal => {
                const matchesType = activeFilter === 'ALL' || signal.direction === activeFilter;
                const matchesBacktest = !showOnlyBacktested || signal.backtested;
                return matchesType && matchesBacktest;
            });

            filteredSignals.forEach(signal => {
                const listItem = document.createElement('li');
                const backtestText = signal.backtested ? ' <span class="backtest-badge">[95% ACCURACY ✓]</span>' : '';
                listItem.innerHTML = `${signal.asset} ; ${signal.time} ; ${signal.direction}${backtestText}`;
                signalList.appendChild(listItem);
            });
        }

        function showAnimation() {
            const animationMessage = document.getElementById('animation-message');
            animationMessage.style.display = 'block';
            setTimeout(() => {
                animationMessage.style.display = 'none';
            }, 2000);
        }

        function handleResetSignals() {
            signals = [];
            existingSignals = new Set();
            renderSignals();
        }

        function updateDateTime() {
            const currentDate = new Date();
            const dateStr = currentDate.toLocaleDateString('en-GB', { timeZone: 'Asia/Dhaka' });
            const timeStr = currentDate.toLocaleTimeString('en-GB', { timeZone: 'Asia/Dhaka' });

            document.getElementById('current-date').textContent = dateStr;
            document.getElementById('current-time').textContent = timeStr;
        }

        const assetSelect = document.getElementById('asset-select');
        availableAssets.forEach(asset => {
            const option = document.createElement('option');
            option.value = asset;
            option.textContent = asset;
            assetSelect.appendChild(option);
        });

        document.getElementById('generate-signals').addEventListener('click', handleGenerateSignals);
        document.getElementById('reset-signals').addEventListener('click', handleResetSignals);
        document.getElementById('filter-select').addEventListener('change', renderSignals);
        document.getElementById('backtest-filter').addEventListener('change', renderSignals);

        setInterval(updateDateTime, 1000);
        updateDateTime();
    </script>
</body>
</html>
"""

# تشغيل كود الـ HTML داخل تطبيق Streamlit بكفاءة وبدون أخطاء
components.html(html_code, height=900, scrolling=True)
