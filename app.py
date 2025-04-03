# app.py (Stock Chart App)
from flask import Blueprint, render_template, request, jsonify
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64
import csv
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

main_bp = Blueprint('main', __name__)

# Load companies from CSV file
COMPANIES = {}
try:
    with open('companies.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            COMPANIES[f"{row['Company Name']} ({row['Ticker Symbol']})"] = row['Ticker Symbol']
except FileNotFoundError:
    print("companies.csv not found")

@main_bp.route('/search')
def search():
    term = request.args.get('term', '').lower()
    matches = [company for company in COMPANIES.keys() if term in company.lower()]
    return jsonify(matches[:5])

@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/analyze', methods=['POST'])
def analyze():
    stocks_input = request.form['stocks'].replace(' ', '').upper()
    stocks = [s for s in stocks_input.split(',') if s][:5]

    plt.switch_backend('Agg')
    period = request.form.get('period', 'ytd')
    today = datetime.today()
    log_scale = request.form.get('log_scale', 'false') == 'true'

    if period == 'ytd':
        start_date = datetime(today.year, 1, 1)
    elif period == '5y':
        start_date = today - relativedelta(years=5)
    elif period == '10y':
        start_date = today - relativedelta(years=10)
    elif period == '15y':
        start_date = today - relativedelta(years=15)
    elif period == '20y':
        start_date = today - relativedelta(years=20)
    elif period == '25y':
        start_date = today - relativedelta(years=25)
    else:
        start_date = datetime(today.year, 1, 1)

    valid_stocks = []
    stock_data = {}
    company_names = {}

    for stock in stocks:
        try:
            ticker = stock.split('(')[-1].split(')')[0]
            company_name = stock.split('(')[0].strip()
            company_names[ticker] = company_name
            print(f"Attempting to download data for: {ticker}")
            data = yf.download(ticker, start=start_date, progress=False)
            if not data.empty:
                stock_data[ticker] = data
                if data.index.tz is None:
                    stock_data[ticker].index = pd.to_datetime(stock_data[ticker].index, utc=True)
                valid_stocks.append(ticker)
            else:
                print(f"No data found for {ticker}")
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    if not valid_stocks:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'No data available'})
        else:
            return render_template('home.html')

    plt.figure(figsize=(12, 6))
    for stock in valid_stocks:
        data = stock_data[stock]
        initial_price = data['Close'].iloc[0]
        percentage_change = (data['Close'] / initial_price) * 100
        plt.plot(data.index, percentage_change, label=company_names[stock])

    plt.title('Stock Price Percentage Change (Initial Price = 100)')
    plt.xlabel('Date')
    plt.ylabel('Percentage of Initial Price')
    if log_scale:
        plt.yscale('log')
    plt.legend()
    plt.grid(True)

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_img = base64.b64encode(img.getvalue()).decode()
    plt.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'chart_img': chart_img})
    else:
        return render_template('home.html', chart_img=chart_img)