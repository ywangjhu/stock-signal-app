from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for frontend requests

# Get API key from environment variable
TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY', '')

@app.route('/')
def home():
    """Serve the frontend HTML"""
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/stock-data')
def get_stock_data():
    """
    Fetch stock data from Twelve Data API
    Query params:
    - symbol: Stock symbol (e.g., QQQ, AAPL)
    - interval: Time interval (default: 1min)
    - outputsize: Number of data points (default: 100)
    """
    try:
        # Get parameters from request
        symbol = request.args.get('symbol', 'QQQ')
        interval = request.args.get('interval', '1min')
        outputsize = request.args.get('outputsize', '100')
        
        # Validate symbol
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        # Check if API key is set
        if not TWELVE_DATA_API_KEY:
            return jsonify({'error': 'API key not configured on server'}), 500
        
        # Make request to Twelve Data API
        url = f'https://api.twelvedata.com/time_series'
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
            'apikey': TWELVE_DATA_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # Check if request was successful
        if response.status_code != 200:
            return jsonify({
                'error': f'Twelve Data API returned status {response.status_code}'
            }), response.status_code
        
        data = response.json()
        
        # Check for API errors
        if 'status' in data and data['status'] == 'error':
            return jsonify({
                'error': data.get('message', 'Unknown API error')
            }), 400
        
        # Return the data
        return jsonify(data)
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request to Twelve Data timed out'}), 504
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Request failed: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/quote')
def get_quote():
    """
    Get current quote for a symbol
    Query params:
    - symbol: Stock symbol
    """
    try:
        symbol = request.args.get('symbol', 'QQQ')
        
        if not TWELVE_DATA_API_KEY:
            return jsonify({'error': 'API key not configured'}), 500
        
        url = f'https://api.twelvedata.com/quote'
        params = {
            'symbol': symbol,
            'apikey': TWELVE_DATA_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'status' in data and data['status'] == 'error':
            return jsonify({'error': data.get('message', 'Unknown error')}), 400
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
