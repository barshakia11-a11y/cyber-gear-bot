import discord
from discord.ext import commands
from discord.ui import Button, View
import firebase_admin
from firebase_admin import credentials, db
import asyncio
from flask import Flask
from threading import Thread
import os

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
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = "כאן_הטוקן_שלך"
LOG_CHANNEL_ID = 1478512328356925571

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="סגור טיקט", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_tkt")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("הערוץ יימחק בעוד 5 שניות...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="פתח טיקט ומשוך הזמנה", style=discord.ButtonStyle.success, custom_id="open_tkt_main", emoji="📩")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        await interaction.response.send_message(f"הטיקט נפתח! {channel.mention}", ephemeral=True)

        users_ref = db.reference('users').get()
        latest_order, buyer_name, buyer_pass, max_time = None, "אורח", "לא ידוע", 0
        if users_ref:
            for uname, udata in users_ref.items():
                if isinstance(udata, dict) and 'last_order' in udata:
                    order = udata['last_order']
                    if order.get('time', 0) > max_time:
                        max_time, latest_order, buyer_name = order['time'], order, uname
                        buyer_pass = udata.get('pass', 'ללא סיסמה')
        if latest_order:
            embed = discord.Embed(title="⚙️ CYBER GEAR - הזמנה", color=0x00f2ff)
            embed.add_field(name="👤 משתמש", value=f"`{buyer_name}`", inline=False)
            embed.add_field(name="📦 מוצרים", value=f"**{latest_order.get('items', 'ריק')}**", inline=False)
            embed.add_field(name="💰 סה\"כ", value=f"**{latest_order.get('total', '₪0')}**", inline=False)
            await channel.send(embed=embed, view=CloseTicketView())
            log_chan = guild.get_channel(LOG_CHANNEL_ID)
            if log_chan:
                log_emb = discord.Embed(title="🔔 הזמנה חדשה", description=f"משתמש: {user.mention}\nערוץ: {channel.mention}", color=0xffcc00)
                await log_chan.send(embed=log_emb)
        else:
            await channel.send("לא נמצאה הזמנה.", view=CloseTicketView())

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    print(f'Bot {bot.user.name} is online!')

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(title="🛍️ סיום רכישה", description="לחץ למטה לפתיחת טיקט", color=0xbc13fe)
    await ctx.send(embed=embed, view=TicketView())

# הפעלה עם מנגנון הגנה נגד חסימות זמניות
keep_alive()
try:
    bot.run(TOKEN)
except discord.errors.HTTPException as e:
    if e.status == 429:
        print("Discord is rate limiting us. Please wait a few minutes or restart the service.")
    else:
        raise e
