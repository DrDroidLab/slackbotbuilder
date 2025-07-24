# AI Slack Bot Builder

A Python-based Slack bot that can process messages, respond to mentions, and automate workflows using AI. Built with FastAPI and designed for extensibility and easy configuration.

## Quick Setup

### 1. Slack App Setup

1. Go to [Slack API Apps](https://api.slack.com/apps) and create a new app
2. Copy the JSON from `slack_manifest.json` and paste it into your app configuration
3. Set the Request URL for Event Subscriptions to: `https://your-domain.com/api/slack/events`
4. Set the Request URL for Interactivity to: `https://your-domain.com/api/slack/interactive`
5. Install the app to your workspace and copy the credentials to `credentials.yaml`

### 2. Install Dependencies

```bash
pip install uv
uv sync
```

### 3. Start the Server

```bash
uv run python app.py
```

The bot will start on `http://localhost:5000`. Make sure this is served by the hostname you have mentioned in the manifest for events subscription.

## Workflow Configuration

Workflows are defined in `workflows.yaml` and allow you to create custom responses based on message patterns:

```yaml
workflows:
  - name: "Sample workflow"
    channel_name: "*"        # Channel name to match (or "*" for any channel)
    user_name: "*"           # User name to match (or "*" for any user)
    wildcard: "hi"           # Wildcard pattern to match in message text
    action_script: "sample_response.py"
    enabled: true
```

### Wildcard Patterns

- **`hi`**: Matches exact word "hi" (case-insensitive)
- **`*hi*`**: Matches any text containing "hi" (e.g., "this", "history")
- **`hi*`**: Matches text starting with "hi" (e.g., "hi there")
- **`*hi`**: Matches text ending with "hi" (e.g., "say hi")

## Sample Usage

### 1. Add Bot to Channel

Create a new channel named "drdroid-slack-bot-tester" and add your bot to that channel

### 2. Send Test Message

Send a message containing "hi" in the channel

### 3. Expected Output

The bot should respond with: "👋 This is a sample response from your Slack bot."

## Health Check

Check the bot status:

```bash
curl http://localhost:5000/api/health
```

## License

MIT License - see LICENSE file for details. 