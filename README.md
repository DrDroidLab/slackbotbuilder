# AI Slack Bot Builder

A Ready-to-use Slack bot connected to LLMs & MCP Servers (Your Data) that can process messages, respond to mentions, and automate workflows.
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
6. Create a channel `drdroid-slack-bot-tester` and add your app to it

### Add or Create an MCP Server

1. Go to `mcp_servers/mcp.json` and add an existing MCP Server Config (URL based, non-authenticated MCP servers are supported at the moment).

Create an MCP Server for Grafana / K8s / Signoz / other tools in 1-click from this [open source project](https://github.com/DrDroidLab/drd-vpc-agent/tree/mcp_main).

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

### Sample Usage
1. Create a new channel named `drdroid-slack-bot-tester` and add your bot to that channel.
2. Send a message `Can you check dashboard X in Grafana? @BotName` in the channel.
3. The bot should respond with: `👋 This is a sample response from your Slack bot.`


## Workflow Configuration

Workflows are defined in `workflows.yaml` and allow you to create custom responses based on message patterns (think alert based automations):

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
- **`app_mention_required`**: Only match if bot is mentioned (optional, default: false)
- **`action_script`**: Script file in the `scripts/` directory (optional)
- **`action_prompt`**: Prompt file in the `prompts/` directory (optional)

### Wildcard Patterns

- **`hi`**: Matches exact word "hi" (case-insensitive)
- **`*hi*`**: Matches any text containing "hi" (e.g., "this", "history")
- **`hi*`**: Matches text starting with "hi" (e.g., "hi there")
- **`*hi`**: Matches text ending with "hi" (e.g., "say hi")

After any changes in the workflows and scripts, restart the server. 

## Health Check

Check the bot status:

```bash
curl <ngrok_url>/api/health
```

## License

MIT License - see LICENSE file for details. 
