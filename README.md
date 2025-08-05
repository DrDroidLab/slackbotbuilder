# DIY AI Debugging Agent Toolkit

![ai_debugging_agent.png](/ai_debugging_agent.png)

This repo is a part of the DIY toolkit to build your own AI Debugging Agent. Spinning up this repo will give you an AI Agent that can:

0. Work with some general purpose intelligence out-of-the-box
1. Leverage scripts, prompts and knowledge base to debug your production issues
2. Access and query monitoring tools configured as MCP servers
3. Interact and respond to user queries from Slack
4. Listen to alerts on Slack and auto-respond to it


## 0. Chatbot mode:
Even if you do not create scripts, prompts or knowledge base, you can still create the AI agent and interact with it via Slack chat by tagging the bot. 

If you add any [monitoring tools' MCP server](github.com/DrDroidLab/monitoring-mcp-servers), it will have access to your monitoring tools and might query them for your query. You can decide to further improve the quality of investigation here.

## 1. Scripts, Runbooks and Prompts:
There are multiple types of AI as well as non-AI automations that you can setup using this toolkit. For example:
- [Agentic investigation of a service latency spike using a runbook written in English language](/prompts/service_latency_spike_analyser.md)
- [AI analysis of logs](/scripts/grafana_non_ai_tool.py).
- Kubernetes cluster [actions in specific situations](/scripts/k8s_auto_restart_tool.py).
- A general purpose agentic investigation WITHOUT any pre-configuration.

Using [workflows](/workflows_readme.MD), rules can be setup on when to trigger what.


## 2. Connecting AI Agent to Monitoring tools

To connect the Agent to monitoring tools, this toolkit supports integration to any MCP Server. Instructions to connect AI Agent to the monitoring tools:
- Go to `mcp_servers/mcp.json` and add an existing MCP Server Config (URL based, non-authenticated MCP servers are supported at the moment).
- Create an MCP Server for Grafana / K8s / Signoz / other tools in 1-click from this [open source project](http://github.com/DrDroidLab/monitoring-mcp-servers/). For trial purposes, you can also use the MCP server mentioned in the monitoring-mcp-servers repo.


## 3. Building the Slack bot to test out everything

### a. Generate a public https url from localhost using ngrok ([Read why](https://chatgpt.com/share/68923cd2-2a28-800d-8115-b8db7cdcb04c)) 

1. Install ngrok: Download from ngrok.com or use a package manager
2. Run your local server: Start your application on a port (e.g., port 5000)
3. Create the tunnel: Run `ngrok http 5000`
4. Get your HTTPS URL: ngrok will provide a free HTTPS URL like `https://abc123.ngrok.io`

### b. Slack App Setup

1. Go to [Slack API Apps](https://api.slack.com/apps) and create a new app
2. Copy the JSON from `slack_manifest.json` and paste it into your app configuration
3. Set the Request URL for Event Subscriptions to: `<ngrok_url>/api/slack/events`
4. Set the Request URL for Interactivity to: `<ngrok_url>/api/slack/interactive`
5. Install the app to your workspace and copy the credentials to `credentials.yaml`
6. Create a channel `drdroid-slack-bot-tester` and add your app to it

### c. Add your OpenAI Key

1. Add your OpenAI key to credentials.yaml

### d. Install Dependencies & Start the server

```bash
pip install uv
uv sync
uv run python app.py
```

The bot will start on `http://localhost:5000`. Your ngrok public url will point to this server.


## Interact with AI Agent
1. Create a new channel named `drdroid-slack-bot-tester` and add your bot to that channel.
2. Send a message `Can you check dashboard X in Grafana? @BotName` in the channel.
3. The bot should respond with: `👋 This is a sample response from your Slack bot.`


# Support:
Reach out to us directly:
-- Discord: https://discord.gg/AQ3tusPtZn
