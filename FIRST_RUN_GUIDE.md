# PC Control Bot - First Run Guide

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Bot for the First Time
```bash
python main.py
```

## 🔑 First Launch Setup

On **first launch**, the bot will:

1. **Request your Telegram Bot Token**
   - If no token is found in environment variables, `.env` file, or `config.json`
   - The bot will prompt you to enter your token interactively

2. **Save the Token**
   - Your token will be automatically saved to `config.json`
   - Next time you run the bot, it will use the saved token

3. **Start All Services**
   - Telegram Bot will start polling
   - Web interface will be available
   - System tray icon will appear (Windows only)

## 📝 Getting Your Telegram Bot Token

1. Open **Telegram** and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create a new bot
4. Copy the token provided by BotFather
5. Paste it when the bot asks during first run

## ✅ Successful Startup

You'll see a message like this:

```
============================================================
✅  BOT STARTED SUCCESSFULLY
============================================================

📊 Services running:
  ✓ Telegram Bot (polling)
  ✓ Web Interface (Flask server)
  ✓ System Tray Icon

💾 Configuration saved to: config.json
📝 Logs saved to: bot.log

============================================================
```

## 🖼️ System Tray

- **Windows**: The bot will appear in your system tray (taskbar)
- **Status**: Shows whether bot is running
- **Quit**: Use tray menu to gracefully shutdown

## 📁 Configuration Files

### `config.json`
- **telegram_token**: Your bot token (saved after first run)
- **allowed_user_ids**: List of Telegram user IDs with access
- **password**: Password for web interface authentication
- **other settings**: Bot-specific configurations

### `bot.log`
- Complete log of all bot activities
- Useful for debugging issues

## 🔒 Security Notes

- **Never share your bot token**
- `config.json` contains sensitive data - keep it safe
- Change the default password before deploying

## ⚙️ Advanced Setup

### Using Environment Variables
You can also set the token via environment variable (highest priority):
```bash
set TELEGRAM_BOT_TOKEN=your_token_here
python main.py
```

### Using .env File
Create a `.env` file:
```
TELEGRAM_BOT_TOKEN=your_token_here
```

Priority order:
1. Environment variable `TELEGRAM_BOT_TOKEN`
2. `.env` file
3. `config.json`
4. Interactive prompt (first run)

## 🐛 Troubleshooting

### "Token seems too short"
- Verify you copied the entire token from BotFather
- Token should be ~40+ characters

### "System tray not available"
- The bot still works, system tray is optional
- On non-Windows systems, tray might not be available

### Web Interface Not Responding
- Check that port 5000 is not in use
- Look at `bot.log` for error messages

## 📞 Support

For issues or questions:
1. Check `bot.log` for error messages
2. Verify your bot token with BotFather
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
