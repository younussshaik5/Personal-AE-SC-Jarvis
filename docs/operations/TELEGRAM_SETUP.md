# Telegram Bot Setup Guide

## What You Get

A full-featured Telegram bot that acts as a chat interface to JARVIS. You can:
- **Chat naturally** with JARVIS about your work
- **Run commands**: /status, /deals, /patterns, /scan, /archive, etc.
- **Receive alerts** about important events (persona switches, approvals, errors)
- **Query data** from your JARVIS CRM in real-time

## Prerequisites

1. A Telegram account
2. Admin access to your channel (if you want broadcasts)
3. python-telegram-bot installed (done via `pip install -e jarvis`)

## 1. Create Your Bot (Already Done)

You already created: **@Innu1bot** with token:
```
YOUR_TELEGRAM_BOT_TOKEN_HERE
```

Store this token securely.

## 2. Configure JARVIS

Edit `jarvis/config/jarvis.yaml` (or create if missing) and add:

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_TELEGRAM_BOT_TOKEN_HERE"
  # List of Telegram user IDs allowed to chat with the bot
  # Get your user ID by messaging @userinfobot
  allowed_user_ids:
    - 123456789  # Replace with your actual Telegram user ID
  # Optional: channel for broadcasts (use @username or numeric ID)
  channel_id: "@your_channel_username"  # or -1001234567890
  broadcast_events: true
  allow_conversational_chat: true
  allow_commands: true
  notify_on_persona_switch: true
  notify_on_modification_approved: true
  notify_on_errors: true
  notify_on_competitors: true
  rate_limit_per_minute: 10
```

**How to get your Telegram user ID:**
- Open Telegram
- Search for `@userinfobot` and start a chat
- It will reply with your numeric user ID
- Add that ID to `allowed_user_ids`

**How to get your channel ID:**
- Add your bot to the channel as an admin
- Send a message to the channel
- Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
- Find the `"chat":{"id": ...}` field in the response
- Use that ID (or if channel has @username, you can use that)

## 3. Restart JARVIS

```bash
# If running via fireup:
./fireup_jarvis.sh

# Or manually:
pkill -f jarvis.core.orchestrator
cd jarvis && nohup python3 -m jarvis.core.orchestrator > ../logs/jarvis.log 2>&1 &
```

Check logs:
```bash
tail -f logs/jarvis.log | grep -i telegram
```

You should see: "Telegram bot configured" and "Telegram bot started and polling"

## 4. Test It

Open Telegram and send a message to your bot:

```
/start
```

You should receive:
```
🚀 JARVIS Online!
I'm your AI assistant, fully integrated with your OpenCode workspace.
...
```

Try other commands:
```
/status
/deals
/patterns
```

Or chat naturally:
```
What's the current persona?
Any competitors detected?
How many patterns have you learned?
```

## 5. Channel Broadcasts (Optional)

If you set `channel_id`, JARVIS will automatically post important events to that channel:
- ✅ Modifications approved
- 👤 Persona switched
- ❌ Errors occurred
- ⚠️ Competitors detected
- 🔍 New patterns discovered

## Commands Reference

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick guide |
| `/status` | System status, active persona, uptime |
| `/persona` | Current persona and available personas |
| `/deals` | List active deals (up to 5) |
| `/patterns` | Learned patterns and statistics |
| `/competitors` | Detected competitors with counts |
| `/scan` | Trigger immediate workspace scan |
| `/archive` | Create a workspace snapshot |
| `/help` | This help message |

**Natural Language:** You can also just type questions like:
- "What deals are active?"
- "Show me patterns"
- "Who are we competing against?"
- "Switch to solution consultant" (if persona switching is enabled)

## Security Notes

- **Only users in `allowed_user_ids` can interact with the bot**. This prevents unauthorized access.
- Bot token is sensitive - anyone with it can control your bot. Never share it.
- Consider using a separate Telegram account for the bot's channel posts.
- The bot will ignore messages from unauthorized users.

## Troubleshooting

**Bot doesn't respond:**
- Check JARVIS logs for "Telegram bot" errors
- Verify bot token is correct and not expired
- Ensure `allowed_user_ids` includes your user ID
- Make sure python-telegram-bot is installed: `pip list | grep python-telegram-bot`
- Check bot is not blocked by @BotFather due to spam

**Channel broadcasts not working:**
- Verify bot is added as admin to the channel
- Check `channel_id` is correct (numeric ID recommended)
- Look for "Failed to send broadcast" in logs

**"Forbidden: bot was blocked by the user":**
- You blocked the bot? Unblock it in Telegram
- Or you used wrong user ID in allowed_user_ids (maybe your ID is different than expected)

**"Conflict: terminated by other getUpdates request":**
- Only one polling should run. If you have multiple instances, kill extras.
- Use `pkill -f "telegram"` and restart JARVIS.

**Import errors:**
```bash
pip install -e jarvis
```

## Advanced: Customizing Responses

To modify the bot's replies, edit the command methods in `jarvis/telegram/bot.py`:
- `_get_status()` → status message
- `_generate_contextual_response()` → AI chat responses
- `_format_event_for_channel()` → broadcast message format

## AI-Powered Responses (Future)

Currently, `_generate_contextual_response` uses pattern matching. To enable true LLM-powered conversations:
1. Add an LLM integration module to JARVIS
2. Modify `_generate_contextual_response` to call that module with workspace context
3. The bot will then answer using your full knowledge base

## Management

**View bot status:**
```bash
# Check if bot process is running
ps aux | grep -i telegram

# Or via JARVIS status (if integrated)
jarvis status
```

**Restart bot:**
```bash
# Through orchestrator restart
pkill -f jarvis.core.orchestrator
# Then start JARVIS again
```

**Stop bot temporarily:**
```bash
pkill -f "python3.*jarvis.telegram"
# Or disable in config: telegram.enabled: false
```

## Support

- Bot API docs: https://core.telegram.org/bots/api
- python-telegram-bot docs: https://docs.python-telegram-bot.org/
- OpenCode/JARVIS docs: See repository README

---

## Next Steps

Now that Telegram is integrated:
- Configure your channel ID for broadcast alerts
- Add team members' user IDs to `allowed_user_ids` for shared access
- Customize message templates to match your style
- Build out missing commands (e.g., /create deal, /switch persona)
- Connect an LLM for intelligent natural language responses

Enjoy controlling JARVIS from anywhere via Telegram!
