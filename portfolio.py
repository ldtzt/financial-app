from flask import Blueprint, request, jsonify
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
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

    portfolio_data = pd.DataFrame()
    for i, stock in enumerate(stocks):
        try:
            stock_data = yf.download(stock, start=five_years_ago, end=today)['Adj Close']
            portfolio_data[stock] = stock_data * allocations[i]
        except Exception as e:
            return jsonify({'error': f'Error fetching data for {stock}: {e}'})

    if portfolio_data.empty:
        return jsonify({'error': 'No data fetched.'})

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

    plt.figure(figsize=(8, 8))
    plt.pie(allocations, labels=stocks, autopct='%1.1f%%')
    plt.title('Portfolio Allocation')

    pie_chart_img = io.BytesIO()
    plt.savefig(pie_chart_img, format='png', bbox_inches='tight')
    pie_chart_img.seek(0)
    pie_chart_base64 = base64.b64encode(pie_chart_img.getvalue()).decode()
    plt.close()

    # Industry Pie Chart
    industries = {}
    for stock in stocks:
        try:
            ticker = yf.Ticker(stock)
            info = ticker.info
            if 'industry' in info:
                industry = info['industry']
                industries[industry] = industries.get(industry, 0) + 1
        except Exception as e:
            print(f"Error getting industry for {stock}: {e}")

    if industries:
        plt.figure(figsize=(8, 8))
        plt.pie(industries.values(), labels=industries.keys(), autopct='%1.1f%%')
        plt.title('Portfolio Industry Allocation')

        industry_pie_chart_img = io.BytesIO()
        plt.savefig(industry_pie_chart_img, format='png', bbox_inches='tight')
        industry_pie_chart_img.seek(0)
        industry_pie_chart_base64 = base64.b6encode(industry_pie_chart_img.getvalue()).decode()
        plt.close()
    else:
        industry_pie_chart_base64 = None

    # Weekly returns heatmap
    weekly_returns = portfolio_returns.resample('W').mean()

    heatmap_data = weekly_returns.to_frame()
    heatmap_data['week'] = heatmap_data.index.isocalendar().week
    heatmap_data['year'] = heatmap_data.index.year
    heatmap_data = heatmap_data.pivot_table(index='year', columns='week', values=0)

    plt.figure(figsize=(16, 8))
    sns.heatmap(heatmap_data, cmap='RdBu', center=0, annot=False, fmt=".2f", linewidths=.5)
    plt.title('Portfolio Weekly Returns Heatmap (Last 5 Years)')
    plt.xlabel('Week')
    plt.ylabel('Year')

    heatmap_img = io.BytesIO()
    plt.savefig(heatmap_img, format='png', bbox_inches='tight')
    heatmap_img.seek(0)
    heatmap_base64 = base64.b64encode(heatmap_img.getvalue()).decode()
    plt.close()

    return jsonify({
        'return_plot': return_plot_base64,
        'pie_chart': pie_chart_base64,
        'industry_pie_chart': industry_pie_chart_base64,
        'heatmap_img': heatmap_base64
    })