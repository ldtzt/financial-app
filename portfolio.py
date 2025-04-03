from flask import Blueprint, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.colors import LinearSegmentedColormap

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/monte_carlo', methods=['POST'])
def monte_carlo():
    stocks_input = request.form['stocks'].replace(' ', '').upper()
    stocks = [s for s in stocks_input.split(',') if s][:5]
    days = int(request.form.get('days', 365 * 5))  # 5 years of days
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

        # Calculate percentage changes from initial price
        initial_price = stock_data[stock].iloc[-1]
        end_prices_pct_change = [(sim[-1] - initial_price) / initial_price * 100 for sim in sim_results]

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), facecolor='black')

        # Simulation plot (top subplot)
        for sim in sim_results:
            ax1.plot(sim, alpha=0.1, color='lightblue')
        ax1.set_title(f'Monte Carlo Simulation for {stock}', color='white')
        ax1.set_xlabel('Days', color='white')
        ax1.set_ylabel('Simulated Price', color='white')
        ax1.tick_params(axis='x', colors='white')
        ax1.tick_params(axis='y', colors='white')
        ax1.spines['bottom'].set_color('white')
        ax1.spines['top'].set_color('white')
        ax1.spines['left'].set_color('white')
        ax1.spines['right'].set_color('white')

        # Histogram plot (bottom subplot)
        n, bins, patches = ax2.hist(end_prices_pct_change, bins=30, rwidth=0.9, edgecolor='black')

        # Apply gradient to bars
        cmap = LinearSegmentedColormap.from_list('mycmap', ['lightblue', 'steelblue'])
        max_n = n.max() if len(n) > 0 else 0
        if max_n > 0:  # Robust check
            for i, patch in enumerate(patches):
                color = cmap(n[i] / max_n)
                patch.set_facecolor(color)

        # Overlay normal distribution curve
        x = np.linspace(min(end_prices_pct_change), max(end_prices_pct_change), 100)
        ax2.plot(x, (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2) * len(end_prices_pct_change) * (bins[1] - bins[0]), color='orange', linewidth=2)

        ax2.set_title(f'End Price % Change Distribution for {stock}', color='white')
        ax2.set_xlabel('End Price % Change', color='white')
        ax2.set_ylabel('Occurrences', color='white')
        ax2.tick_params(axis='x', colors='white')
        ax2.tick_params(axis='y', colors='white')
        ax2.spines['bottom'].set_color('white')
        ax2.spines['top'].set_color('white')
        ax2.spines['left'].set_color('white')
        ax2.spines['right'].set_color('white')

        # Save the combined plot to a BytesIO object
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', facecolor='black')
        img.seek(0)
        chart_img = base64.b64encode(img.getvalue()).decode()
        plt.close(fig)

        results[stock] = chart_img

    return jsonify(results)