import discord
from discord.ext import commands
from discord.ui import Button, View
import firebase_admin
from firebase_admin import credentials, db
import asyncio

# 1. חיבור ל-Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cybergear-7a90c-default-rtdb.europe-west1.firebasedatabase.app/'
    })

# 2. הגדרות הבוט
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# שים לב: מומלץ להחליף את הטוקן הזה כי הוא נחשף בשיחה
TOKEN = "MTQ3ODU0MzM5NDI3NTA2NTk4OA.GINQXx.x8Mutt5WhIjdmkQ6C_r2ToAN2QfiPIDDLw1lME"

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="סגור טיקט", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("הערוץ יימחק בעוד 5 שניות...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="פתח טיקט ומשוך הזמנה", style=discord.ButtonStyle.success, custom_id="open_ticket_final", emoji="📩")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        
        # יצירת חדר פרטי
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        await interaction.response.send_message(f"הטיקט נפתח בהצלחה! {channel.mention}", ephemeral=True)

        # משיכת נתונים מה-Firebase
        users_ref = db.reference('users').get()
        latest_order = None
        buyer_name = "אורח"
        buyer_pass = "לא ידוע"
        max_time = 0

        if users_ref:
            for uname, udata in users_ref.items():
                if isinstance(udata, dict):
                    order = udata.get('last_order')
                    if order and isinstance(order, dict):
                        order_time = order.get('time', 0)
                        if order_time > max_time:
                            max_time = order_time
                            latest_order = order
                            buyer_name = uname
                            buyer_pass = udata.get('pass', 'ללא סיסמה')

        if latest_order:
            embed = discord.Embed(
                title="⚙️ CYBER GEAR - פרטי הזמנה מזוהה",
                description=f"שלום {user.mention}, מצאנו את ההזמנה האחרונה שבוצעה באתר:",
                color=0x00f2ff
            )
            embed.add_field(name="👤 שם משתמש באתר", value=f"**`{buyer_name}`**", inline=False)
            embed.add_field(name="🔑 סיסמה", value=f"||**`{buyer_pass}`**||", inline=False)
            embed.add_field(name="📦 מוצרים", value=f"**{latest_order.get('items', 'ריק')}**", inline=False)
            embed.add_field(name="💰 סה\"כ לתשלום", value=f"**{latest_order.get('total', '₪0')}**", inline=False)
            embed.set_footer(text="הזמנה זו זוהתה אוטומטית לפי זמן ביצוע")
            
            await channel.send(embed=embed, view=CloseTicketView())
        else:
            await channel.send(
                content=f"שלום {user.mention}, לא מצאתי הזמנה חדשה ב-Firebase.",
                view=CloseTicketView()
            )

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    print(f'--- {bot.user.name} Is Online & Ready! ---')

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🛍️ סיום רכישה - CYBER GEAR",
        description="לחץ על הכפתור למטה כדי לפתוח טיקט פרטי.\nהבוט ימשוך אוטומטית את פרטי ההזמנה האחרונה שלך.",
        color=0xbc13fe
    )
    await ctx.send(embed=embed, view=TicketView())

bot.run(TOKEN)