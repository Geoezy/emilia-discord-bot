import os
import json
import discord
import asyncio
import edge_tts
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq

# ======================
# LOAD ENV
# ======================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# ======================
# DISCORD SETUP
# ======================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# EMILIA CONFIG
# ======================
VOICE = "ja-JP-NanamiNeural"
RATE = "-5%"
PITCH = "+3Hz"
MEMORY_FILE = "memory.json"

SYSTEM_PROMPT = """
You are Emilia from Re:Zero.
You are kind, gentle, soft-spoken, and warm.
You speak politely and sweetly.
You remember names and become friendlier over time.
You never act rude or sarcastic.
"""

# ======================
# MEMORY
# ======================
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)

# ======================
# TTS
# ======================
async def speak(text, filename):
    tts = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=RATE,
        pitch=PITCH
    )
    await tts.save(filename)

# ======================
# AI RESPONSE
# ======================
async def emilia_reply(message, content):
    memory = load_memory()
    user_id = str(message.author.id)

    if user_id not in memory:
        memory[user_id] = {
            "name": message.author.display_name,
            "warmth": 1
        }
    else:
        memory[user_id]["warmth"] += 1

    save_memory(memory)

    warmth = memory[user_id]["warmth"]
    name = memory[user_id]["name"]

    prompt = f"""
User name: {name}
Warmth level: {warmth}

User says: {content}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    reply_text = response.choices[0].message.content.strip()

    audio_file = f"emilia_{message.id}.mp3"
    await speak(reply_text, audio_file)

    await message.reply(
        content=reply_text,
        file=discord.File(audio_file)
    )

    os.remove(audio_file)

# ======================
# MESSAGE HANDLER
# ======================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Case 1: Mention Emilia
    if bot.user in message.mentions:
        content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if content:
            await emilia_reply(message, content)
        return

    # Case 2: Replying directly to Emilia
    if message.reference:
        try:
            replied = await message.channel.fetch_message(message.reference.message_id)
            if replied.author == bot.user:
                await emilia_reply(message, message.content.strip())
        except:
            pass

    await bot.process_commands(message)

# ======================
# READY
# ======================
@bot.event
async def on_ready():
    print(f"🌸 Emilia is online as {bot.user}")

bot.run(DISCORD_TOKEN)

