
from flask import Flask, render_template, request
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    stocks = request.form['stocks'].replace(' ', '').upper().split(',')[:5]
    
    plt.figure(figsize=(12, 6))
    for stock in stocks:
        data = yf.download(stock, start='2023-01-01', progress=False)
        plt.plot(data.index, data['Close'], label=stock)
    
    plt.title('Stock Price Comparison')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.grid(True)
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_img = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return render_template('home.html', chart_img=chart_img)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
