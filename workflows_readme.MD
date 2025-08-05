## Workflow Configuration

Workflows are defined in `workflows.yaml` and allow you to create custom responses based on message patterns (think alert based automations):

```yaml
workflows:
  - name: "Sample workflow"
    channel_name: "*"        # Channel name to match (or "*" for any channel)
    user_name: "*"           # User name to match (or "*" for any user)
    wildcard: "hi"           # Wildcard pattern to match in message text
    action_script: "sample_response.py" # Script
    action_prompt: "prompt.md" #
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