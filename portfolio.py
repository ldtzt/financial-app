# portfolio.py
from flask import Blueprint, request, jsonify

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/calculate', methods=['POST'])
def calculate_portfolio():
    portfolio = {}
    total_allocation = 0
    for key, value in request.form.items():
        if key.startswith('stock'):
            stock_num = int(key[5:])
            stock = value
            allocation = int(request.form.get(f'allocation{stock_num}', 0))
            portfolio[stock] = allocation
            total_allocation += allocation

    if total_allocation != 100:
        return jsonify({'error': 'Total allocation must be 100%'})

    return jsonify(portfolio)