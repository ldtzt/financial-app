from flask import Flask, render_template, request, jsonify
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64
import csv
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

app = Flask(__name__)

# Load companies from CSV file
COMPANIES = {}
try:
    with open('companies.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            COMPANIES[f"{row['Company Name']} ({row['Ticker Symbol']})"] = row['Ticker Symbol']
except FileNotFoundError:
    print("companies.csv not found")

@app.route('/search')
def search():
    term = request.args.get('term', '').lower()
    matches = [company for company in COMPANIES.keys() if term in company.lower()]
    return jsonify(matches[:5])

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    stocks_input = request.form['stocks'].replace(' ', '').upper()
    stocks = [s for s in stocks_input.split(',') if s][:5]  # Filter out empty strings
    
    # Set matplotlib to use Agg backend
    plt.switch_backend('Agg')
    period = request.form.get('period', 'ytd')
    today = datetime.today()

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
    company_names = {} # added this dict

    for stock in stocks:
        try:
            ticker = stock.split('(')[-1].split(')')[0]
            company_name = stock.split('(')[0].strip() # added this line
            company_names[ticker] = company_name # added this line
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
        return render_template('home.html')

    plt.figure(figsize=(12, 6))
    for stock in valid_stocks:
        data = stock_data[stock]
        initial_price = data['Close'].iloc[0]
        percentage_change = (data['Close'] / initial_price) * 100 # removed -1 and added *100
        plt.plot(data.index, percentage_change, label=company_names[stock]) # company names in legend.

    plt.title('Stock Price Percentage Change (Initial Price = 100)')
    plt.xlabel('Date')
    plt.ylabel('Percentage of Initial Price')
    plt.legend()
    plt.grid(True)

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_img = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template('home.html', chart_img=chart_img)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)