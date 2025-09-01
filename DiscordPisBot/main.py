import discord
from discord.ext import commands, tasks
import logging
from GetApiInfo.api_main import getGamesInfo
from datetime import datetime, time
import json
from pathlib import Path
import json, os, tempfile, asyncio

TOKEN=''

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

setdaily_target_channel = None

SAVE_FILE = Path("sent_games_data.json")
id_dict = dict()
save_lock = asyncio.Lock()
loop_lock = asyncio.Lock()

def load_id_dict():
    global id_dict

    if SAVE_FILE.exists():
        try:
            with open("sent_games_data.json", "r", encoding="utf-8") as f:
                id_dict = json.load(f)
        except (json.JSONDecodeError, OSError):
            id_dict = {}
    else:
        id_dict = {}
    
def atomic_save(data:dict, path:Path):
    dirpath = path.parent or Path('.')
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
            json.dump(data, tmpf, indent=2, ensure_ascii=False)
            tmpf.flush()
            os.fsync(tmpf.fileno())
        os.replace(tmp_path, str(path))

    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

async def save_id_dict():
    async with save_lock:
        atomic_save(id_dict, SAVE_FILE)

@bot.event
async def on_ready():
    print("*"*20)
    print("Bot has started")
    print("*"*20)
    load_id_dict()
    daily_task.start()

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, id=1329885426525143140)
    if role:
        await member.add_roles(role)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

@bot.command()
async def setdaily(ctx):
    guild = ctx.guild
    if guild.roles[-1] in ctx.author.roles:
        global setdaily_target_channel
        setdaily_target_channel = ctx.channel
        await ctx.send("Ежже")
    else:
        await ctx.send("Братишка прав не хватает")

# Zeit anpassen, id_dict anpasen
@tasks.loop(minutes=1)
async def daily_task():
    global setdaily_target_channel
    global id_dict

    if loop_lock.locked():
        return

    async with loop_lock:
        if setdaily_target_channel is None:
            return
           
        now = datetime.now().time()
        today = datetime.today().weekday()
        target = time(22,52)

        test_mode = False

        if not test_mode:
            if not (now.hour == target.hour and now.minute == target.minute):
                return

        gamesList = getGamesInfo()

        for game_data in gamesList:
        
            game_id = str(game_data['id']) # als String für JSON-Keys

            # Falls key nicht existiert -> get -> None
            current = id_dict.get(game_id) # None oder Integer (0..6)

            if current is None:
                id_dict[game_id] = today
                await save_id_dict()

                embed = discord.Embed(
                    title=game_data["title"],
                    description=f"""
Стоимость: {game_data["worth"]}
Описание: {game_data["description"]}
Платформы: {game_data["platforms"]}
Дата оканчания акции: {game_data["end_date"]}
Ссылка: {game_data["open_giveaway"]}
""",
                    colour=0x800080,)
            
                embed.set_image(url=game_data["thumbnail"])
                await setdaily_target_channel.send(embed=embed)

            elif current == today:
                id_dict.pop(game_id, None)
                await save_id_dict()
            else:
                pass

@daily_task.before_loop
async def before_daily_task():
    await bot.wait_until_ready()


bot.run(TOKEN, log_level=logging.DEBUG)
