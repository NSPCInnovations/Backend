from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api', methods=['POST'])
def handle_request():
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        # Process data (Example: Echo back with a message)
        response = {
            'message': 'Received your request',
            'received_data': data
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)