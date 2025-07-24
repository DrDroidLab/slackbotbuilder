from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import os
from datetime import datetime
from slack_events import slack_event_handler
from slack_credentials_manager import credentials_manager
from workflow_manager import workflow_manager

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    credentials_summary = credentials_manager.get_credentials_summary()
    workflows_summary = workflow_manager.get_workflows_summary()
    return jsonify({
        "status": "healthy", 
        "message": "AI Slack Bot Builder is running",
        "credentials": credentials_summary,
        "workflows": workflows_summary
    })

# Slack Interactive endpoint
@app.route('/api/slack/interactive', methods=['POST'])
def handle_slack_interactive():
    """Handle Slack interactive components"""
    try:
        # For now, just return a success response
        # This can be expanded later for handling interactive components
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/slack/events', methods=['POST'])
def handle_slack_events():
    """Handle Slack event subscriptions"""
    try:
        request_data = request.get_json()
        return slack_event_handler.handle_event(request_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 