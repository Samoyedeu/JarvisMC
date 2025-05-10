# JarvisMC

JarvisMC is a Discord bot designed specifically for the Basement Gang's Minecraft Server.
It automates tasks like server status updates, command handling, and backup operations to enhance the Minecraft experience through Discord integration.

## Features

- 🟢 Start and stop Minecraft server
- 📦 Backup server files (with checks to avoid data corruption)
- 👥 Check online players
- 📊 Report server status
- 🧠 Natural language command support using fuzzy matching and semantic similarity
- 🛑 Shutdown the bot remotely
- 🔐 Restricted commands based on authorized user ID

## Configuration

Create a `config.json` file in the same directory with the following keys:

```json
{
  "TOKEN": "YOUR_DISCORD_BOT_TOKEN",
  "RCON_HOST": "localhost",
  "RCON_PORT": "your_rcon_port",
  "RCON_PASSWORD": "your_rcon_password",
  "SERVER_DIR": "path_to_your_server_directory",
  "START_SCRIPT": "start_server.bat",
  "BACKUP_DEST": "path_to_backup_folder",
  "AUTHORIZED_USER_ID": DISCORD_USER_ID
}
```

## Requirements

- Python 3.7+
- Packages:
  - `discord.py`
  - `mcrcon`
  - `fuzzywuzzy`
  - `spacy`
  - `en_core_web_sm` model for spaCy

Install dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Run

To start the bot:

```bash
python -m bot.py
```

Make sure your Minecraft server allows RCON and is configured properly.

## Commands

- `@bot startserver` - Starts the Minecraft server
- `@bot stopserver` - Stops the Minecraft server
- `@bot status` - Checks server status
- `@bot check_players` - Lists currently online players
- `@bot backup` - Backs up the server (when offline)
- `@bot terminatejarvis` - Shuts down the bot (admin only)

## Smart Command Parsing

Bot listens for a wide variety of natural language phrases (like "open the gates", "power down", etc.) and matches them to appropriate commands using both fuzzy matching and semantic similarity.
