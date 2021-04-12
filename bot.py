import logging
from asyncio import sleep

import discord
from discord.ext import commands
from config import SETTINGS
from crew import crew_embed
from diary import diary_embed
from film import film_embed
from helpers import LetterboxdError
from list_ import list_embed
from review import review_embed
from user import user_embed
from roulette import random_embed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%m/%d %H:%M:%S')

bot = commands.Bot(command_prefix='!', case_insensitive=True)
bot.remove_command('help')

@bot.event
async def on_ready():
    logging.info(
        'Logged in %d servers as %s' % (len(bot.guilds), bot.user.name))
    bot.loop.create_task(update_stats())


@bot.event
async def on_message(message):
    if message.content.startswith('!'):
        message.content = message.content.replace('’', '').replace('‘', '')
        await bot.process_commands(message)


async def update_stats():
    while True:
        await bot.change_presence(
            activity=discord.Game('!helplb - {} servers'.format(
                len(bot.guilds))))
        await sleep(900)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('This command requires a parameter.')
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send('This command requires the {} permission.'.format(
                ', '.join(err for err in error.missing_perms)))
    elif isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
        return
    elif isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, discord.HTTPException):
            return
    else:
        await ctx.send('Sorry, the command crashed. :/')
        logging.error(ctx.message.content)
        raise error


async def send_msg(ctx, msg):
    if isinstance(msg, discord.Embed):
        await ctx.send(embed=msg)
    else:
        await ctx.send(msg)


# Commands


@bot.command()
async def helplb(ctx):
    help_embed = discord.Embed(colour=discord.Color.from_rgb(54, 57, 62))
    help_embed.set_thumbnail(url='https://i.imgur.com/Kr1diFu.png')
    help_embed.set_author(
        name='Letterboxd Bot', icon_url='https://i.imgur.com/5VALKVy.jpg')
    help_embed.set_footer(
        text='Maintained & hosted by Vito#1929. For support, please join https://discord.gg/HunZVZQz9d',
        icon_url='https://i.imgur.com/h0CaAv4.png')
    for key, value in SETTINGS['help'].items():
        help_embed.add_field(name=key, value=value, inline=False)
    help_embed.description = 'Invite Bot | '\
        + '[GitHub](https://github.com/velzerat/lb-bot)'
    await ctx.send(embed=help_embed)


@bot.command(aliases=['u'])
async def user(ctx, username):
    try:
        msg = await user_embed(username)
    except LetterboxdError as err:
        msg = err
    await send_msg(ctx, msg)


@bot.command(aliases=['d'])
async def diary(ctx, username):
    try:
        msg = await diary_embed(username)
    except LetterboxdError as err:
        msg = err
    await send_msg(ctx, msg)


@bot.command(aliases=['actor', 'actress', 'director', 'c'])
async def crew(ctx, *, arg):
    try:
        msg = await crew_embed(arg, ctx.invoked_with)
    except LetterboxdError as err:
        msg = err
    await send_msg(ctx, msg)


@bot.command(aliases=['movie', 'kino', 'f'])
async def film(ctx, *, arg):
    try:
        # eiga.me ratings for specific servers
        if ctx.guild and ctx.guild.id in SETTINGS['mkdb_servers']:
            msg = await film_embed(arg, True)
        else:
            msg = await film_embed(arg)
    except LetterboxdError as err:
        msg = err
    await send_msg(ctx, msg)


async def check_if_two_args(ctx):
    msg = ctx.message.content.split()
    if len(msg) < 3:
        await ctx.send('This command requires 2 parameters.')
    return len(msg) > 2

@bot.command(aliases=['list', 'l'])
@commands.check(check_if_two_args)
async def list_(ctx, username, *args):
    try:
        msg = await list_embed(username, ' '.join(str(i) for i in args))
    except LetterboxdError as err:
        msg = err
    await send_msg(ctx, msg)


@bot.command(name='roulette')
async def roulette(ctx):
    try:
        msg = await random_embed()
    except LetterboxdError as err:
        msg = err
    await send_msg(ctx, msg)


@bot.command(aliases=['entry', 'r'])
@commands.check(check_if_two_args)
async def review(ctx, username, *args):
    try:
        msg = await review_embed(username, ' '.join(str(i) for i in args))
    except LetterboxdError as err:
        msg = err
    await send_msg(ctx, msg)


@bot.command(name='del')
@commands.bot_has_permissions(manage_messages=True)
async def delete(ctx):
    await ctx.message.delete()
    found_bot_msg = False
    found_usr_cmd = False
    cmd_list = list()
    for command in bot.commands:
        cmd_list.append('!' + command.name)
        for alias in command.aliases:
            cmd_list.append('!' + alias)

    async for log_message in ctx.channel.history(limit=30):
        if log_message.author.id == bot.user.id and not found_bot_msg:
            bot_message = log_message
            found_bot_msg = True
        elif found_bot_msg:
            if log_message.content:
                first_word = log_message.content.split()[0]
            else:
                continue
            if first_word in cmd_list:
                found_usr_cmd = True
                cmd_message = log_message
                break

    if found_usr_cmd:
        if not ctx.author.permissions_in(ctx.channel).manage_messages:
            if not cmd_message.author.id == ctx.author.id:
                return
        await cmd_message.delete()
        await bot_message.delete()


bot.run(SETTINGS['discord'])
