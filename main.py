import asyncio
from config import *

import discord
from discord.ext import commands

from Watchlist import Watchlist

watch = Watchlist()
bot = commands.Bot(command_prefix=commands.when_mentioned_or(*['!']))
cogs = [
    'cogs.watch'
]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} with ID {bot.user.id}')
    await bot.change_presence(activity=discord.Game(' Flipping 0.1 -> 0.01'))

def main():
    for cog in cogs:
        try:
            bot.load_extension(cog)
        except Exception as e:
            print(f"Failed to load cog {cog}\nWith error: {e}")

    bot.run(DISCORD_TOKEN)

if __name__ == '__main__':
    main()
