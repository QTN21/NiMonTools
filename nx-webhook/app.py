import logging
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='app.log', encoding='utf-8', level=logging.INFO)

@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    data = request.json  # Get the JSON data from the incoming request
    # Process the data and perform actions based on the event
    print("Received webhook data:", data)
    logging.info(f"Received webhook data: {json.dumps(data)}")
    return jsonify({'message': 'Webhook received successfully'}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
