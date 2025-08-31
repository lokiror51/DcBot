import discord
from discord.ext import commands, tasks
import logging
from GetApiInfo.api_main import getGamesInfo
from datetime import datetime, time

TOKEN=''

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

setdaily_target_channel = None

id_dict = dict()

@bot.event
async def on_ready():
    print("*"*20)
    print("Bot has started")
    print("*"*20)
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

    if setdaily_target_channel is None:
        return
    
    now = datetime.now().time()
    today = datetime.today().weekday()
    target = time(21,27)

    if now.hour == target.hour and now.minute == target.minute:
        gamesList = getGamesInfo()

        for game_data in gamesList:

            id_dict.setdefault(game_data['id'], None)

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

            if id_dict[game_data['id']] != today:
                id_dict[game_data['id']] = today
                await setdaily_target_channel.send(embed=embed) 
            else:
                id_dict.pop(game_data['id'])

@daily_task.before_loop
async def before_daily_task():
    await bot.wait_until_ready()

bot.run(TOKEN, log_level=logging.DEBUG)