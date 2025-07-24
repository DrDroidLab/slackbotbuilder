# AI Slack Bot Builder

A Python-based Slack bot that can process messages, respond to mentions, and automate workflows using AI. Built with Flask and designed for extensibility and easy configuration.

## Features

- **Message Processing**: Handles incoming messages and app mentions with intelligent routing
- **Event Subscriptions**: Listens to various Slack events (channel creation, member joins, etc.)
- **Interactive Components**: Supports interactive elements like buttons and modals
- **Credential Management**: Secure YAML-based credential storage with validation
- **Workflow System**: Configurable workflows that match messages and execute custom scripts
- **Health Monitoring**: Built-in health check endpoints with detailed status information
- **Multi-App Support**: Architecture designed to support multiple Slack apps (currently configured for single app)
- **Security**: Request signature verification and timestamp validation
- **Logging**: Comprehensive logging for debugging and monitoring

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Your Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Enter your app name and select your workspace
4. Copy the JSON from `slack_manifest.json` and paste it into your app configuration

### 3. Configure Credentials

Run the setup script to configure your Slack app credentials:

```bash
python setup_credentials.py
```

This will guide you through entering:
- App ID
- App Name
- Signing Secret
- Bot User OAuth Token

### 4. Configure Your Slack App

In your Slack app settings:

1. **Event Subscriptions**: Set the Request URL to your events endpoint
2. **Interactivity & Shortcuts**: Set the Request URL to your interactive endpoint
3. **OAuth & Permissions**: Install the app to your workspace
4. **Basic Information**: Copy the credentials to your `credentials.yaml`

### 5. Run the Bot

```bash
python app.py
```

The bot will start on `http://localhost:5000`

## Configuration

### Credentials File Structure

The `credentials.yaml` file contains:

```yaml
slack:
  app_id: "YOUR_APP_ID"
  app_name: "AI Slack Bot"
  signing_secret: "YOUR_SIGNING_SECRET"
  bot_token: "xoxb-YOUR_BOT_TOKEN"

api:
  base_url: "https://slack.com/api"
  timeout: 30
```

### Single App Configuration

The current schema supports a single Slack app configuration. The architecture is designed to support multiple apps, but currently configured for a single app setup.

## Workflow System

The bot includes a powerful workflow system that allows you to define custom responses based on message patterns.

### Workflow Configuration

Workflows are defined in `workflows.yaml`:

```yaml
workflows:
  - name: "hello_response"
    channel_name: "*"        # Channel name to match (or "*" for any channel)
    user_name: "*"           # User name to match (or "*" for any user)
    wildcard: "hi"           # Wildcard pattern to match in message text
    action_script: "hello_response.py"
    enabled: true
```

### Workflow Parameters

- **name**: Unique identifier for the workflow
- **channel_name**: Channel name to match (use "*" for any channel)
- **user_name**: User name to match (use "*" for any user)
- **wildcard**: Wildcard pattern to match in message text
- **action_script**: Path to the script in the `scripts/` directory
- **enabled**: Whether the workflow is active (true/false)

### Wildcard Patterns

The wildcard system supports simple pattern matching:
- **`hi`**: Matches exact word "hi" (case-insensitive)
- **`*hi*`**: Matches any text containing "hi" (e.g., "this", "history")
- **`hi*`**: Matches text starting with "hi" (e.g., "hi there", "history")
- **`*hi`**: Matches text ending with "hi" (e.g., "say hi", "oh hi")
- **`?hi`**: Matches text with any single character before "hi" (e.g., "ahi", "bhi")

### Action Scripts

Action scripts are Python files in the `scripts/` directory that:

1. Receive the Slack message JSON as a command line argument
2. Process the message and generate a response
3. Return a JSON response with the following structure:

```python
{
    "text": "Response message",
    "channel": "channel_id",
    "thread_ts": "timestamp",  # Optional: reply in thread
    "response_type": "in_channel"  # or "ephemeral"
}
```

### Sample Scripts

- **`hello_response.py`**: Responds with "hi 👋" when someone says hello

### Creating Custom Scripts

1. Create a new Python file in the `scripts/` directory
2. Make it executable: `chmod +x scripts/your_script.py`
3. Add a workflow configuration in `workflows.yaml`
4. The script will receive the Slack message JSON as `sys.argv[1]`

## API Endpoints

### Health Check
- **GET** `/api/health` - Check bot status and credentials

### Slack Events
- **POST** `/api/slack/events` - Handle Slack event subscriptions

### Slack Interactive
- **POST** `/api/slack/interactive` - Handle interactive components

## Development

### Project Structure

```
slackbotbuilder/
├── app.py                      # Main Flask application
├── slack_events.py             # Slack event handlers with signature verification
├── slack_credentials_manager.py # Credential management and validation
├── workflow_manager.py          # Workflow management and execution
├── slack_manifest.json         # Slack app manifest with required scopes
├── credentials.yaml            # Credentials (create this)
├── workflows.yaml              # Workflow configurations
├── scripts/                    # Action scripts directory
│   └── hello_response.py       # Sample hello response script
├── setup_credentials.py        # Setup script
├── requirements.txt            # Python dependencies
└── README.md                  # This file
```

### Core Components

#### SlackEventHandler (`slack_events.py`)
- Handles all Slack event types (messages, app mentions, channel events, etc.)
- Verifies request signatures for security
- Processes messages through the workflow system
- Manages bot responses and interactions

#### WorkflowManager (`workflow_manager.py`)
- Loads and manages workflow configurations
- Matches messages against workflow patterns
- Executes action scripts and processes responses
- Provides workflow status and summary information

#### SlackCredentialsManager (`slack_credentials_manager.py`)
- Manages YAML-based credential storage
- Validates credential completeness
- Provides secure access to app configurations
- Supports credential reloading

### Adding New Event Handlers

1. Create a handler method in `SlackEventHandler` class
2. Add the event type to the main `handle_event` method
3. Update your Slack app configuration to subscribe to the new event

### Testing

1. Use ngrok for local development:
   ```bash
   ngrok http 5000
   ```

2. Update your webhook URLs with the ngrok URL

3. Test the bot by mentioning it in a channel

## Troubleshooting

### Common Issues

1. **Invalid Signature**: Check that your signing secret is correct
2. **Bot Not Responding**: Ensure the bot is invited to the channel
3. **Webhook Errors**: Verify your webhook URLs are accessible
4. **Permission Issues**: Check that all required scopes are added

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

Check the bot status:

```bash
curl http://localhost:5000/api/health
```

## Security

- Credentials are stored in YAML files (not in code)
- Signing verification prevents request forgery
- Timestamp validation prevents replay attacks
- No sensitive data is logged
- Request signature verification for all Slack events

## Dependencies

- **Flask**: Web framework for the API server
- **PyYAML**: YAML configuration file handling
- **requests**: HTTP client for Slack API calls
- **flask-cors**: CORS support for web requests
- **hmac/hashlib**: Security signature verification

## License

MIT License - see LICENSE file for details. 