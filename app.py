from flask import Flask, render_template, request, jsonify
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64
import csv

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
    matches = [company for company in COMPANIES.keys()
                if term in company.lower()]
    return jsonify(matches[:5])

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    stocks_input = request.form['stocks'].replace(' ', '').upper()
    stocks = stocks_input.split(',')[:5]
    valid_stocks = []
    for stock in stocks:
        try:
            data = yf.download(stock, start='2023-01-01', progress=False)
            if not data.empty:
                valid_stocks.append(stock)
        except Exception as e:
            print(f"Error fetching data for {stock}: {e}")

    if not valid_stocks:
        return render_template('home.html')

    plt.figure(figsize=(12, 6))
    for stock in valid_stocks:
        data = yf.download(stock, start='2023-01-01', progress=False)
        plt.plot(data.index, data['Close'], label=stock)

    plt.title('Stock Price Comparison')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
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