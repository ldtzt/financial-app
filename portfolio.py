# filepath: c:\Users\leodu\Desktop\Financial APP\portfolio.py
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend

from flask import Blueprint, request, jsonify
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.colors as mcolors
from pytz import UTC
from datetime import datetime
from dateutil.relativedelta import relativedelta
import seaborn as sns

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/calculate', methods=['POST'])
def calculate_portfolio():
    data = request.form
    stocks = []
    allocations = []

    for key, value in data.items():
        if key.startswith('stock'):
            stocks.append(value)
        elif key.startswith('allocation'):
            allocations.append(int(value) / 100)

    if not stocks or not allocations:
        return jsonify({'error': 'Please add stocks and allocations.'})

    if len(stocks) != len(allocations):
        return jsonify({'error': 'Number of stocks and allocations must match.'})

    today = datetime.now()
    five_years_ago = today - relativedelta(years=5)
    five_years_ago = (datetime.now() - relativedelta(years=5)).replace(tzinfo=UTC)
    portfolio_weekly_returns = portfolio_weekly_returns[portfolio_weekly_returns.index >= five_years_ago]

    company_names = {}
    stock_data = {}
    portfolio_data = pd.DataFrame()

    for stock in stocks:
        try:
            ticker = stock.split('(')[-1].split(')')[0]
            company_name = stock.split('(')[0].strip()
            company_names[ticker] = company_name
            print(f"Attempting to download data for: {ticker}")

            data = yf.download(ticker, start=five_years_ago, progress=False, auto_adjust=False)
            print(f"Data for {ticker}:")
            print(data.head())

            if not data.empty:
                stock_data[ticker] = data

                if data.index.tz is None:
                    stock_data[ticker].index = pd.to_datetime(stock_data[ticker].index, utc=True)

                allocation_index = stocks.index(stock)
                portfolio_data[ticker] = data['Adj Close'] * allocations[allocation_index]
            else:
                print(f"No data found for {ticker}")
        except Exception as e:
            print(f"Error fetching data for {stock} ({ticker}): {e}")

    if portfolio_data.empty:
        return jsonify({'error': 'No data fetched.'})

    # Portfolio Cumulative Returns
    portfolio_returns = portfolio_data.sum(axis=1).pct_change().dropna()
    cumulative_returns = (1 + portfolio_returns).cumprod() * 100

    plt.figure(figsize=(12, 6))
    plt.plot(cumulative_returns)
    plt.title('Portfolio Cumulative Returns (Last 5 Years)')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns (%)')
    plt.grid(True)

    return_plot_img = io.BytesIO()
    plt.savefig(return_plot_img, format='png', bbox_inches='tight')
    return_plot_img.seek(0)
    return_plot_base64 = base64.b64encode(return_plot_img.getvalue()).decode()
    plt.close()

    # Portfolio Allocation Pie Chart
    plt.figure(figsize=(8, 8))
    labels = [company_names[stock.split('(')[-1].split(')')[0]] for stock in stocks]
    colors = list(mcolors.TABLEAU_COLORS.values())
    plt.pie(allocations, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
    plt.title('Portfolio Allocation')

    pie_chart_img = io.BytesIO()
    plt.savefig(pie_chart_img, format='png', bbox_inches='tight')
    pie_chart_img.seek(0)
    pie_chart_base64 = base64.b64encode(pie_chart_img.getvalue()).decode()
    plt.close()

    # Weekly Returns Heatmap for the Overall Portfolio
    # Calculate the overall portfolio weekly returns
    portfolio_weekly_returns = portfolio_data.resample('W').sum().pct_change().dropna()

    # Ensure we only include the past 5 years of weekly returns
    five_years_ago = datetime.now() - relativedelta(years=5)
    portfolio_weekly_returns = portfolio_weekly_returns[portfolio_weekly_returns.index >= five_years_ago]

    # Generate heatmap for overall portfolio weekly returns
    plt.figure(figsize=(12, 6))
    sns.heatmap(
        portfolio_weekly_returns.to_frame().T,  # Convert to DataFrame and transpose for heatmap
        annot=False,
        cmap='coolwarm',
        cbar=True,
        xticklabels=portfolio_weekly_returns.index.strftime('%Y-%m-%d'),
        yticklabels=["Portfolio"]
    )
    plt.title('Portfolio Weekly Returns Heatmap (Last 5 Years)')
    plt.xlabel('Date')
    plt.ylabel('')

    heatmap_img = io.BytesIO()
    plt.savefig(heatmap_img, format='png', bbox_inches='tight')
    heatmap_img.seek(0)
    heatmap_base64 = base64.b64encode(heatmap_img.getvalue()).decode()
    plt.close()

    return jsonify({
        'return_plot': return_plot_base64,
        'pie_chart': pie_chart_base64,
        'heatmap_img': heatmap_base64
    })