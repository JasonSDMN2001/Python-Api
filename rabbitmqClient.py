from flask import Flask, request, jsonify
import pika
import json

app = Flask(__name__)

with open("RabbitMQ_Settings.json", "r") as file:
    config = json.load(file)
    rabbitmq_config = config["RabbitMQ"]

@app.route("/connect", methods=["POST"])
def publish_to_rabbitmq():
    try:
        message = request.get_json(force=True) 
        credentials = pika.PlainCredentials(rabbitmq_config['Username'], rabbitmq_config['Password'])
        parameters = pika.ConnectionParameters(host=rabbitmq_config['Host'],
                                               port=rabbitmq_config['Port'],
                                               virtual_host=rabbitmq_config['VirtualHost'],
                                               credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='metadata-ai-queue')
        
        channel.basic_publish(exchange='',
                              routing_key='metadata-ai-queue',
                              body=json.dumps(message))
        connection.close()
        
        return jsonify({"message": "Successfully published to RabbitMQ", "content": message}), 200
    except Exception as e:
        return jsonify({"error": "Failed to publish to RabbitMQ", "original_error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
