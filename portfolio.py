# portfolio.py (Portfolio Builder App)
from flask import Blueprint, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/monte_carlo', methods=['POST'])
def monte_carlo():
    stocks_input = request.form['stocks'].replace(' ', '').upper()
    stocks = [s for s in stocks_input.split(',') if s][:5]
    days = int(request.form.get('days', 365))
    simulations = int(request.form.get('simulations', 100))

    valid_stocks = []
    stock_data = {}
    for stock in stocks:
        try:
            ticker = stock.split('(')[-1].split(')')[0]
            data = yf.download(ticker, period='5y', progress=False)
            if not data.empty:
                stock_data[ticker] = data['Close']
                valid_stocks.append(ticker)
            else:
                print(f"No data found for {ticker}")
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    if not valid_stocks:
        return jsonify({'error': 'No data available'})

    results = {}
    for stock in valid_stocks:
        returns = stock_data[stock].pct_change().dropna()
        mu = returns.mean()
        sigma = returns.std()
        sim_results = []
        for _ in range(simulations):
            prices = [stock_data[stock].iloc[-1]]
            for _ in range(days):
                prices.append(prices[-1] * (1 + np.random.normal(mu, sigma)))
            sim_results.append(prices)
        results[stock] = sim_results

    return jsonify(results)