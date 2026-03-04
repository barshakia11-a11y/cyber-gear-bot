import discord
from discord.ext import commands
import firebase_admin
from firebase_admin import credentials, db
import asyncio
from flask import Flask
from threading import Thread
import aiohttp

# שרת Keep Alive
app = Flask('')
@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# חיבור ל-Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cybergear-7a90c-default-rtdb.europe-west1.firebasedatabase.app/'
    })

intents = discord.Intents.all()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # כאן אנחנו מאלצים את הבוט להשתמש בהגדרות חיבור נקיות
        self.session = aiohttp.ClientSession()
        print("Setup hook complete.")

    async def on_ready(self):
        print(f'Bot {self.user.name} is online and bypass attempts active!')

bot = MyBot()
TOKEN = "MTQ3ODU0MzM5NDI3NTA2NTk4OA.Gs_nD7.7bjGbIzQRyxySbI0zYLrpLxdvZ2a7uJFZmzPJw"

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.send("הבוט מוכן! (כאן יבוא ה-Embed שלך)")

# הרצה עם ניסיון מעקף
keep_alive()
try:
    bot.run(TOKEN)
except discord.errors.HTTPException as e:
    if e.status == 429:
        print("Still rate limited. Render is being blocked by Discord. Try 'Manual Deploy' in 15 minutes.")
    else:
        print(f"Error: {e}")
