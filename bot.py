import discord
from discord.ext import commands
from mcrcon import MCRcon
import subprocess
import socket
import asyncio
import json
from fuzzywuzzy import fuzz
import spacy
import os
import shutil
import datetime

# --- CONFIGURATION ---
with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["TOKEN"]
RCON_HOST = config["RCON_HOST"]
RCON_PORT = config["RCON_PORT"]
RCON_PASSWORD = config["RCON_PASSWORD"]
SERVER_DIR = config["SERVER_DIR"]
START_SCRIPT = config["START_SCRIPT"]
BACKUP_DEST = config["BACKUP_DEST"]
AUTHORIZED_USER_ID = config["AUTHORIZED_USER_ID"]

# Load spaCy model for semantic similarity
nlp = spacy.load("en_core_web_sm")

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)

# --- FLAG VARIABLES ---
is_backup_in_progress = False
is_starting = False
is_stopping = False

# --- FUNCTION TO CHECK IF SERVER IS ONLINE ---
def is_server_online():
    try:
        with socket.create_connection((RCON_HOST, RCON_PORT), timeout=2):
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                mcr.command("list")
            return True
    except:
        return False
    
# --- FUNCTION TO UPDATE BOT PRESENCE ---
async def update_presence():
    if is_server_online():
        await bot.change_presence(activity=discord.Game(name="🟢 Minecraft Server is ON"))
    else:
        await bot.change_presence(activity=discord.Game(name="🔴 Minecraft Server is OFF"))

@bot.command()
async def backup(ctx):
    global is_backup_in_progress
    if is_server_online():
        await ctx.send("⚠️ The server is currently online, sir. Please stop it before backing up to avoid corruption.")
        return

    if is_backup_in_progress:
        await ctx.send("⚠️ A backup is already in progress. Please wait until it finishes.")
        return

    try:
        is_backup_in_progress = True
        await ctx.send("🛠️ Initiating backup routine")

        # Use Popen for non-blocking process execution
        process = subprocess.Popen(['python', 'backup.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Read stdout and stderr
        stdout, stderr = await asyncio.to_thread(process.communicate)

        # Check the result
        if process.returncode == 0:
            await ctx.send(f"Backup completed successfully!")
        else:
            await ctx.send(f"Backup failed")
            print(f"Backup failed: {stderr.decode()}")
    finally:
        is_backup_in_progress = False  # Reset the flag when done

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    
    # Check if the server is online and update bot presence accordingly
    await update_presence()

# --- STATUS COMMAND ---
@bot.command()
async def status(ctx):
    if is_server_online():
        await ctx.send("🟢 The server is currently *ONLINE*, sir.")
        await update_presence()      
    else:
        await ctx.send("🔴 I regret to inform you, the server is *OFFLINE* at the moment.")

@bot.command()
async def startserver(ctx):
    global is_starting
    if is_server_online():
        await ctx.send("⚠️ The server is already operational, sir.")
        await update_presence()  # Update presence to reflect the server state
        return  # Don't proceed with the start logic if it's already online

    if is_starting:
        await ctx.send("⚠️ The server is already starting. Please wait until it's operational.")
        return

    try:
        is_starting = True
        # If the server is offline, start it
        subprocess.Popen(["start", "cmd", "/K", START_SCRIPT], shell=True)
        await ctx.send("🟢 At your command. Initializing the Minecraft server. Please stand by...")
        await asyncio.sleep(6)  # Wait for the server to start
        await ctx.send("🟢 The server is now operational, sir.")
        await update_presence()  # Update presence to reflect the server is now online
    finally:
        is_starting = False  # Reset the flag when done

@bot.command()
async def check_players(ctx):   
    if not is_server_online():
        await ctx.send("⚠️ The server is not yet operational, sir.")
        return

    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command("list")
            await ctx.send(f"🟢 {response}")
    except Exception as e:
        await ctx.send(f"⚠️ An error occurred while checking players: {e}")     

@bot.command()
async def stopserver(ctx):
    global is_stopping
    if not is_server_online():
        await ctx.send("⚠️ The server is not yet operational, sir.")
        return

    if is_stopping:
        await ctx.send("⚠️ The server is already stopping. Please wait until the process is complete.")
        return

    try:
        is_stopping = True
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            mcr.command("stop")
        await ctx.send("🔴 Understood. Issuing shutdown sequence to the server.")
        await asyncio.sleep(6)
        await update_presence()
    finally:
        is_stopping = False  # Reset the flag when done

@bot.command()
async def terminatejarvis(ctx):
    if ctx.author.id == AUTHORIZED_USER_ID:
        await ctx.send("🔴 *Shutting down...* Goodbye, sir.")
        await bot.close()
    else:
        await ctx.send("❌ *Access denied.* Only authorized personnel can initiate shutdowns.")

# --- HANDLE BOTH FUZZY MATCHING AND SEMANTIC SIMILARITY ---
def get_similarity(phrase, command_phrases):
    # Fuzzy matching score (0 to 100)
    best_fuzzy_match = max([fuzz.partial_ratio(phrase, cmd) for cmd in command_phrases])
    
    # Semantic similarity using spaCy
    phrase_doc = nlp(phrase)
    similarity_scores = [phrase_doc.similarity(nlp(cmd)) for cmd in command_phrases]
    best_semantic_similarity = max(similarity_scores)
    
    # Combine the results
    combined_score = (best_fuzzy_match + best_semantic_similarity * 100) / 2
    return combined_score

# --- ON MESSAGE EVENT ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        content = message.content.lower()
    else:
        # Skip processing if the bot is not mentioned
        return
    
    # Greeting Phrases (to greet the bot)
    greeting_phrases = [
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy", "yo", "sup", "greetings"
    ]    

    # Start Server Phrases (to turn the server on)
    start_server_phrases = [
        "open the gates", "power up", "boot up", "start", "start this thing up", "launch", 
        "ignite", "fire up", "bring it online", "activate", "wake up", "initiate", 
        "turn on", "boot the system", "get it running", "power on", "open",
        "start the server", "bring the server online", "boot the server up", "fire up the server",
        "get the server running", "bring it to life", "kickstart the server", "open up the server",
        "run the server", "activate the server", "power up the server", "let's go online",
        "bring it back online", "initiate the server", "let the server run", "let's get it started", "start"
    ]

    # Stop Server Phrases (to shut the server down)
    close_server_phrases = [
        "shut the gates", "close it down", "shut down", "power down", "turn off", 
        "stop", "terminate", "deactivate", "put it to sleep", "hibernate", "power off",
        "shut everything down", "end the session", "turn it off", "go to sleep", "close",
        "shut the server down", "turn off the server", "shut the system", "power off the server",
        "turn the server off", "cut the power", "end the server session", "terminate the server",
        "stop the machine", "deactivate the server", "power down the system", "close the server",
        "shutdown sequence", "take the server offline", "stop the operation", "halt the server", "yamete kudasai", "yamete", "stop",
    ]

    # Help phrases
    help_phrases = [
        "help", "assist me", "what can you do", "commands", "list commands", 
        "i need help", "what are your functions", "how do i use you", 
        "show me your commands", "help me out", "can you help me", "jarvis help"
    ]

    check_players_phrases = ["check players", "who's online", "list players", "show me the players", "player list", "who's in the game", 
    "who's playing", "current players", "active players", "players online", "show me who's online", "list of players", "check current players", "who's unemployed", "check current players", "who's gaming"]

    # Status Phrases (to check the status of the server)
    status_phrases = [
        "status report", "check status", "server status", "how's the server", "is the server online", 
        "is the server up", "server health", "current server state", "server status check", "is it on",
        "stats", "status", "server status check", "what’s the server status", "is the server up and running",
        "server health check", "is the server online or offline", "check the server", "how is the server",
        "current server status", "how’s the server doing", "is the server active", "what’s the server state",
        "server condition check", "can you check if the server is up", "what’s the condition of the server"
    ]

    # Shutdown/Terminate Jarvis Phrases (to shut down the bot)
    terminate_jarvis_phrases = [
        "shut yourself down", "turn off Jarvis", "power down Jarvis", "terminate yourself", "end the bot session",
        "stop Jarvis", "close the bot", "shutdown Jarvis", "quit Jarvis", "end the bot", "end yourself", "clean state protocol"
    ]

    # Check for fuzzy match + semantic similarity score
    greeting_score = get_similarity(content, greeting_phrases)
    help_score = get_similarity(content, help_phrases)
    start_score = get_similarity(content, start_server_phrases)
    stop_score = get_similarity(content, close_server_phrases)
    status_score = get_similarity(content, status_phrases)
    terminate_jarvis_score = get_similarity(content, terminate_jarvis_phrases)
    check_players_score = get_similarity(content, check_players_phrases)

    # Threshold to decide whether the command is strong enough to trigger
    threshold = 60  # You can adjust this value
    greeting_help_threshold = 50 

    if start_score > threshold:
        ctx = await bot.get_context(message)
        await startserver(ctx)
        return

    if stop_score > threshold:
        ctx = await bot.get_context(message)
        await stopserver(ctx)
        return
    
    if status_score > threshold:
        ctx = await bot.get_context(message)
        await status(ctx)
        return
    
    if terminate_jarvis_score > threshold:
        ctx = await bot.get_context(message)
        await terminatejarvis(ctx)
        return
    
    if help_score > greeting_help_threshold:
        help_message = (
        "**🛠️ Available Commands:**\n"
        "`@Jarvis start` – Starts the Minecraft server.\n"
        "`@Jarvis stop` – Stops the Minecraft server.\n"
        "`@Jarvis status` – Checks if the server is online.\n"
        "`@Jarvis terminate` – Shuts me (the bot) down. Only available to Mr. Stark\n\n"
        "You can also say things like:\n"
        "- *\"Open the gates\"* to start the server\n"
        "- *\"Shut the gates\"* to stop the server\n"
        "- *\"Is the server up?\"* to check status\n"
        "- *\"Assemble the Avengers\"* for a fun surprise 😉\n"
    )
        await message.channel.send(help_message)
        return
    
    if check_players_score > threshold:
        ctx = await bot.get_context(message)
        await check_players(ctx)
        return
    
    if greeting_score > greeting_help_threshold:
        # Respond to the greeting
        await message.channel.send(f"Hello {message.author.name}! How can I assist you today?")
        return
    
    if terminate_jarvis_score > threshold:
        ctx = await bot.get_context(message)
        await terminatejarvis(ctx)
        return

    if "assemble the avengers" in content:
        ctx = await bot.get_context(message)
        await ctx.send("@everyone 🛡️ *Initiating Protocol: Avenger Assembly.*\nAll units, report for duty. This is not a drill.")
        return

    await bot.process_commands(message)

# --- RUN BOT ---
bot.run(TOKEN)