import discord
from discord.ext import commands
from discord.ui import Button, View
import os, json, random, asyncio, time

# ========= CONFIG =========
PREFIX = "a"
DATA_PATH = "data/"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ========= JSON =========
def load(file, default):
    path = DATA_PATH + file
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(file, data):
    with open(DATA_PATH + file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

eco = load("economia.json", {})
vip = load("vip.json", [])
emojis = load("emojis_rinha.json", [])
blacklist = load("blacklist.json", [])

# ========= ECONOMIA =========
def user(uid):
    return eco.get(str(uid), {"carteira": 0})

def set_user(uid, valor):
    eco[str(uid)] = {"carteira": valor}
    save("economia.json", eco)

def add_money(uid, valor):
    set_user(uid, user(uid)["carteira"] + valor)

def remove_money(uid, valor):
    set_user(uid, max(0, user(uid)["carteira"] - valor))

# ========= ANTI-SPAM =========
cooldowns = {}

def anti_spam(uid, limite=5, tempo=10):
    agora = time.time()
    lista = cooldowns.get(uid, [])
    lista = [t for t in lista if agora - t < tempo]
    lista.append(agora)
    cooldowns[uid] = lista
    return len(lista) > limite

# ========= EMBED =========
def emb(title, desc, vip_user=False):
    cor = discord.Color.gold() if vip_user else discord.Color.pink()
    return discord.Embed(title=title, description=desc, color=cor)

# ========= READY =========
@bot.event
async def on_ready():
    print(f"🟢 Bot online como {bot.user}")

# ========= HELP COM BOTÕES =========
class HelpView(View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="💰 Economia", style=discord.ButtonStyle.primary)
    async def eco(self, interaction, button):
        await interaction.response.edit_message(embed=emb(
            "💰 Economia",
            "`asaldo`\n`adaily`\n`acrime`"
        ))

    @discord.ui.button(label="🎮 Jogos", style=discord.ButtonStyle.success)
    async def jogos(self, interaction, button):
        await interaction.response.edit_message(embed=emb(
            "🎮 Jogos",
            "`ablackjack <valor>`\n`arifa <valor>`"
        ))

    @discord.ui.button(label="🥊 Rinha", style=discord.ButtonStyle.danger)
    async def rinha(self, interaction, button):
        await interaction.response.edit_message(embed=emb(
            "🥊 Rinha",
            "`arinha <valor> <limite>`\n`aentrar`"
        ))

    @discord.ui.button(label="💎 VIP", style=discord.ButtonStyle.secondary)
    async def vipb(self, interaction, button):
        await interaction.response.edit_message(embed=emb(
            "💎 VIP",
            "+50% moedas\nCooldown menor\n`avipemoji`"
        ))

    @discord.ui.button(label="👑 ADM", style=discord.ButtonStyle.secondary)
    async def adm(self, interaction, button):
        await interaction.response.edit_message(embed=emb(
            "👑 Administração",
            "`aaddcoins`\n`aremovecoins`\n`agivevip`"
        ))

@bot.command()
async def help(ctx):
    await ctx.send(embed=emb(
        "🌸 Central de Ajuda",
        f"Prefixo: `{PREFIX}`\nUse os botões abaixo"
    ), view=HelpView())

# ========= ECONOMIA =========
@bot.command()
async def saldo(ctx):
    u = user(ctx.author.id)
    await ctx.send(embed=emb("💰 Saldo", f"{u['carteira']} moedas", ctx.author.id in vip))

@bot.command()
async def daily(ctx):
    if anti_spam(ctx.author.id): return
    ganho = random.randint(100_000, 500_000)
    if ctx.author.id in vip:
        ganho = int(ganho * 1.5)
    add_money(ctx.author.id, ganho)
    await ctx.send(embed=emb("🎁 Daily", f"+{ganho} moedas", ctx.author.id in vip))

@bot.command()
async def crime(ctx):
    if anti_spam(ctx.author.id): return
    ganho = random.randint(100_000, 500_000)
    if ctx.author.id in vip:
        ganho = int(ganho * 1.5)
    add_money(ctx.author.id, ganho)
    await ctx.send(embed=emb("🚓 Crime", f"+{ganho} moedas", ctx.author.id in vip))

# ========= RINHA =========
rinha = None

@bot.command()
async def rinha(ctx, valor: int, limite: int):
    global rinha
    if limite > 50:
        return await ctx.send("❌ Máximo 50 pessoas")
    rinha = {"valor": valor, "limite": limite, "players": []}
    await ctx.send(embed=emb("🏁 Rinha criada", "Use `aentrar`"))

@bot.command()
async def entrar(ctx):
    global rinha
    if not rinha: return
    if ctx.author.id not in rinha["players"]:
        rinha["players"].append(ctx.author.id)
    if len(rinha["players"]) >= rinha["limite"]:
        vencedor = random.choice(rinha["players"])
        premio = rinha["valor"] * len(rinha["players"])
        add_money(vencedor, premio)
        await ctx.send(embed=emb("🏆 Vencedor", f"<@{vencedor}> ganhou {premio}"))
        rinha = None

# ========= RIFA =========
rifa = None

@bot.command()
async def rifa(ctx, valor: int):
    global rifa
    rifa = {"valor": valor, "players": []}
    await ctx.send(embed=emb("🎟️ Rifa criada", "Use `aentrar_rifa`"))

@bot.command()
async def entrar_rifa(ctx):
    global rifa
    if not rifa: return
    rifa["players"].append(ctx.author.id)
    if len(rifa["players"]) >= 5:
        vencedor = random.choice(rifa["players"])
        premio = rifa["valor"] * len(rifa["players"])
        add_money(vencedor, premio)
        await ctx.send(embed=emb("🏆 Rifa", f"<@{vencedor}> ganhou {premio}"))
        rifa = None

# ========= BLACKJACK =========
@bot.command()
async def blackjack(ctx, valor: int):
    if user(ctx.author.id)["carteira"] < valor:
        return await ctx.send("❌ Saldo insuficiente")
    remove_money(ctx.author.id, valor)
    cartas = [random.randint(1, 11), random.randint(1, 11)]
    total = sum(cartas)
    if total >= 21:
        ganho = valor * 2
        add_money(ctx.author.id, ganho)
        await ctx.send(embed=emb("🃏 Blackjack", f"BLACKJACK! +{ganho}"))
    else:
        await ctx.send(embed=emb("🃏 Blackjack", f"Cartas: {cartas} | Total: {total}"))

# ========= VIP =========
@bot.command()
@commands.has_permissions(administrator=True)
async def givevip(ctx, membro: discord.Member):
    if membro.id not in vip:
        vip.append(membro.id)
        save("vip.json", vip)
        await ctx.send("💎 VIP concedido")

@bot.command()
async def vipemoji(ctx, emoji: str):
    if ctx.author.id not in vip:
        return await ctx.send("❌ Apenas VIP")
    emojis.append(emoji)
    save("emojis_rinha.json", emojis)
    await ctx.send("🎭 Emoji adicionado")

# ========= ADM =========
@bot.command()
@commands.has_permissions(administrator=True)
async def addcoins(ctx, membro: discord.Member, valor: int):
    add_money(membro.id, valor)
    await ctx.send("👑 Moedas adicionadas")

@bot.command()
@commands.has_permissions(administrator=True)
async def removecoins(ctx, membro: discord.Member, valor: int):
    remove_money(membro.id, valor)
    await ctx.send("👑 Moedas removidas")

# ========= START =========
bot.run(os.getenv("TOKEN"))
