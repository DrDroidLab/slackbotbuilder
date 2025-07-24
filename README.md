# AI Slack Bot Builder

A Ready-to-use Slack bot that can process messages, respond to mentions, and automate workflows using AI. Built with FastAPI and designed for extensibility and easy configuration.

## Quick Setup

### 1. Generate a public https url from localhost (using ngrok)

1. Install ngrok: Download from ngrok.com or use a package manager
2. Run your local server: Start your application on a port (e.g., port 5000)
3. Create the tunnel: Run `ngrok http 5000`
4. Get your HTTPS URL: ngrok will provide a free HTTPS URL like `https://abc123.ngrok.io`

### 2. Slack App Setup

1. Go to [Slack API Apps](https://api.slack.com/apps) and create a new app
2. Copy the JSON from `slack_manifest.json` and paste it into your app configuration
3. Set the Request URL for Event Subscriptions to: `<ngrok_url>/api/slack/events`
4. Set the Request URL for Interactivity to: `<ngrok_url>/api/slack/interactive`
5. Install the app to your workspace and copy the credentials to `credentials.yaml`


### 3. Install Dependencies

```bash
pip install uv
uv sync
```

### 4. Start the Server

```bash
uv run python app.py
```

The bot will start on `http://localhost:5000`. Your ngrok public url will point to this server.

## Workflow Configuration

Workflows are defined in `workflows.yaml` and allow you to create custom responses based on message patterns:

```yaml
workflows:
  - name: "Sample workflow"
    channel_name: "*"        # Channel name to match (or "*" for any channel)
    user_name: "*"           # User name to match (or "*" for any user)
    wildcard: "hi"           # Wildcard pattern to match in message text
    action_script: "sample_response.py"
    app_mention_required: true        # Only match if bot is mentioned
```

### Workflow Fields

- **`name`**: Display name for the workflow (optional)
- **`channel_name`**: Only match in this specific channel (optional)
- **`user_name`**: Only match from this specific user (optional)
- **`wildcard`**: Pattern to match in message text (optional)
- **`action_script`**: Script file in the `scripts/` directory (required)
- **`app_mention_required`**: Only match if bot is mentioned (optional, default: false)

### Wildcard Patterns

- **`hi`**: Matches exact word "hi" (case-insensitive)
- **`*hi*`**: Matches any text containing "hi" (e.g., "this", "history")
- **`hi*`**: Matches text starting with "hi" (e.g., "hi there")
- **`*hi`**: Matches text ending with "hi" (e.g., "say hi")

After any changes in the workflows and scripts, restart the server. 

### Sample Usage
1. Create a new channel named `drdroid-slack-bot-tester` and add your bot to that channel
2. Send a message containing `hi` in the channel
3. The bot should respond with: `👋 This is a sample response from your Slack bot.`

## Health Check

Check the bot status:

```bash
curl <ngrok_url>/api/health
```

## License

MIT License - see LICENSE file for details. 