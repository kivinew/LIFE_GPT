#!/usr/bin/env python3
"""Investment analysis web interface with Telegram integration."""

import os
import json
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

# Telegram bot integration
try:
    from telegram import Bot, Update
    from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
except ImportError:
    print("Warning: python-telegram-bot not installed, Telegram notifications disabled")
    bot = None
    dispatcher = None

# Configuration
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '')

if not BOT_TOKEN:
    print("Warning: TELEGRAM_BOT_TOKEN not set")
    BOT_TOKEN = ""

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dispatcher = Dispatcher(bot, update_queue=None, workers=0) if bot else None

app = Flask(__name__)
CORS(app)

# In-memory storage for investment data
investment_data = {
    'transactions': [],
    'portfolio': {},
    'summary': {
        'total_invested': 0.0,
        'current_value': 0.0,
        'total_return': 0.0,
        'total_return_percent': 0.0
    }
}

# HTML template for the web interface
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Analysis Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f7f9;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .section { background: white; margin-bottom: 20px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { 
            background: #fff; 
            border: 1px solid #e1e8f0; 
            border-radius: 6px; 
            padding: 15px; 
        }
        .card h3 { margin-top: 0; color: #2c3e50; }
        .input-group { margin-bottom: 15px; }
        .input-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .input-group input, .input-group textarea { 
            width: 100%; 
            padding: 8px; 
            border: 1px solid #dcdfe6; 
            border-radius: 4px; 
            font-size: 14px;
        }
        .btn { 
            display: inline-block; 
            padding: 8px 16px; 
            background: #3498db; 
            color: white; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 14px;
            margin-right: 10px;
        }
        .btn-secondary { background: #95a5a6; }
        .btn-success { background: #2ecc71; }
        .btn-danger { background: #e74c3c; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #e1e8f0; }
        th { background: #f8f9fa; }
        .status { padding: 5px 10px; border-radius: 4px; margin: 5px 0; }
        .status-ok { background: #d5f5e3; color: #27ae60; }
        .status-warning { background: #fef9e7; color: #f39c12; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Investment Analysis Dashboard</h1>
        
        <div class="section">
            <h3>📥 Add Transaction</h3>
            <div class="input-group">
                <label>Asset Symbol</label>
                <input type="text" id="symbol" placeholder="AAPL, GOOGL, etc.">
            </div>
            <div class="input-group">
                <label>Type (buy/sell)</label>
                <select id="type">
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                </select>
            </div>
            <div class="input-group">
                <label>Quantity</label>
                <input type="number" id="quantity" placeholder="100">
            </div>
            <div class="input-group">
                <label>Price ($)</label>
                <input type="number" id="price" step="0.01" placeholder="150.25">
            </div>
            <div class="input-group">
                <label>Date (YYYY-MM-DD)</label>
                <input type="date" id="date" value="{{ today }}">
            </div>
            <button class="btn btn-success" onclick="addTransaction()">Add Transaction</button>
        </div>
        
        <div class="section">
            <h3>📊 Portfolio Summary</h3>
            <div class="grid">
                <div class="card">
                    <h4>Total Invested</h4>
                    <div id="total-invested">$0.00</div>
                </div>
                <div class="card">
                    <h4>Current Value</h4>
                    <div id="current-value">$0.00</div>
                </div>
                <div class="card">
                    <h4>Total Return</h4>
                    <div id="total-return">$0.00</div>
                </div>
                <div class="card">
                    <h4>Return %</h4>
                    <div id="return-percent">0.00%</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h3>📋 Transaction History</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Asset</th>
                        <th>Type</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="transaction-table">
                    <!-- Dynamic rows -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let editingId = null;
        
        function addTransaction() {
            const symbol = document.getElementById('symbol').value.trim();
            const type = document.getElementById('type').value;
            const quantity = parseFloat(document.getElementById('quantity').value) || 0;
            const price = parseFloat(document.getElementById('price').value) || 0;
            const date = document.getElementById('date').value;
            
            if (!symbol || quantity <= 0 || price <= 0) {
                alert('Пожалуйста, заполните все поля корректно');
                return;
            }
            
            fetch('/api/transaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, type, quantity, price, date })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadTransactions();
                    updateSummary();
                    // Clear form
                    document.getElementById('symbol').value = '';
                    document.getElementById('quantity').value = '';
                    document.getElementById('price').value = '';
                } else {
                    alert('Ошибка: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => console.error('Error:', error));
        }
        
        function deleteTransaction(id) {
            fetch(`/api/transaction/${id}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadTransactions();
                    updateSummary();
                } else {
                    alert('Ошибка при удалении');
                }
            })
            .catch(error => console.error('Error:', error));
        }
        
        function loadTransactions() {
            fetch('/api/transactions')
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('transaction-table');
                tbody.innerHTML = '';
                data.transactions.forEach((tx, index) => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${tx.date}</td>
                        <td>${tx.symbol}</td>
                        <td>${tx.type}</td>
                        <td>${tx.quantity}</td>
                        <td>$${tx.price.toFixed(2)}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="deleteTransaction(${index})">Удалить</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            })
            .catch(error => console.error('Error loading transactions:', error));
        }
        
        function updateSummary() {
            fetch('/api/summary')
            .then(response => response.json())
            .then(data => {
                document.getElementById('total-invested').textContent = '$' + data.summary.total_invested.toFixed(2);
                document.getElementById('current-value').textContent = '$' + data.summary.current_value.toFixed(2);
                document.getElementById('total-return').textContent = '$' + data.summary.total_return.toFixed(2);
                const percent = data.summary.total_return_percent;
                document.getElementById('return-percent').textContent = percent.toFixed(2) + '%';
                document.getElementById('return-percent').className = percent >= 0 ? 'status status-ok' : 'status status-warning';
            })
            .catch(error => console.error('Error updating summary:', error));
        }
        
        // Initial load
        window.onload = function() {
            loadTransactions();
            updateSummary();
        };
    </script>
</body>
</html>
"""

# Flask routes
@app.route('/')
def index():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template_string(HTML_TEMPLATE, today=today)

@app.route('/api/transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()
    if not data or not data.get('symbol'):
        return jsonify({'success': False, 'error': 'Symbol required'})
    
    transaction = {
        'id': len(investment_data['transactions']),
        'symbol': data['symbol'].upper(),
        'type': data.get('type', 'buy'),
        'quantity': float(data.get('quantity', 0)),
        'price': float(data.get('price', 0)),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d'))
    }
    
    investment_data['transactions'].append(transaction)
    
    # Update portfolio
    symbol = transaction['symbol']
    if symbol not in investment_data['portfolio']:
        investment_data['portfolio'][symbol] = {'total_quantity': 0, 'total_cost': 0, 'entries': []}
    
    portfolio_entry = investment_data['portfolio'][symbol]
    portfolio_entry['total_quantity'] += transaction['quantity']
    portfolio_entry['total_cost'] += transaction['quantity'] * transaction['price']
    portfolio_entry['entries'].append(transaction)
    
    # Recalculate summary
    recalculate_summary()
    
    # Notify Telegram if configured
    notify_telegram(f"📈 Новая транзакция: {symbol} {transaction['type'].upper()} {transaction['quantity']} шт. по ${transaction['price']:.2f}")
    
    return jsonify({'success': True, 'transaction': transaction})

@app.route('/api/transaction/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    if 0 <= tx_id < len(investment_data['transactions']):
        tx = investment_data['transactions'].pop(tx_id)
        
        # Rebuild portfolio from remaining transactions
        investment_data['portfolio'] = {}
        for t in investment_data['transactions']:
            symbol = t['symbol']
            if symbol not in investment_data['portfolio']:
                investment_data['portfolio'][symbol] = {'total_quantity': 0, 'total_cost': 0, 'entries': []}
            portfolio_entry = investment_data['portfolio'][symbol]
            portfolio_entry['total_quantity'] += t['quantity']
            portfolio_entry['total_cost'] += t['quantity'] * t['price']
            portfolio_entry['entries'].append(t)
        
        recalculate_summary()
        notify_telegram(f"🗑️ Удалена транзакция: {tx['symbol']} {tx['type'].upper()} {tx['quantity']} шт. по ${tx['price']:.2f}")
        
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Transaction not found'})

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    return jsonify({'transactions': investment_data['transactions'], 'summary': investment_data['summary']})

@app.route('/api/summary', methods=['GET'])
def get_summary():
    return jsonify({'summary': investment_data['summary']})

def recalculate_summary():
    total_invested = sum(t['quantity'] * t['price'] for t in investment_data['transactions'] if t['type'] == 'buy')
    total_value = sum(
        inv_data['total_cost'] if t['type'] == 'buy' else 0 
        for t in investment_data['transactions'] 
        for inv_data in [investment_data['portfolio'].get(t['symbol'], {'total_cost': 0})]
        if t['type'] == 'buy'
    )
    
    # Simpler calculation - just use current portfolio values
    total_invested = 0
    total_value = 0
    for symbol, data in investment_data['portfolio'].items():
        total_invested += data['total_cost']
        # Current value estimation - in real app would use market prices
        total_value += data['total_cost']  # Placeholder: same as cost for now
    
    total_return = total_value - total_invested
    total_return_percent = (total_return / total_invested * 100) if total_invested > 0 else 0
    
    investment_data['summary'] = {
        'total_invested': round(total_invested, 2),
        'current_value': round(total_value, 2),
        'total_return': round(total_return, 2),
        'total_return_percent': round(total_return_percent, 2)
    }

def notify_telegram(message):
    """Send message to Telegram chat."""
    if not bot or not ADMIN_CHAT_ID:
        return
    try:
        import asyncio
        asyncio.run(bot.send_message(chat_id=ADMIN_CHAT_ID, text=message))
    except Exception as e:
        print(f"Telegram notification error: {e}")

# Initialize on startup
def init_data():
    """Load existing data or initialize empty."""
    recalculate_summary()
    notify_telegram("🚀 Investment dashboard started")

if __name__ == '__main__':
    # Initialize data
    init_data()
    
    # Get port from environment or default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting Investment Dashboard on port {port}")
    print(f"📊 Web interface: http://localhost:{port}")
    print(f"📱 Telegram notifications: {'Enabled' if bot else 'Disabled'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)