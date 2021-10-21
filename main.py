"""
TODO

- Fix the two errors that are currently avoided on line 66. Make it never crash
- Add ability to fetch unverified contracts (Only issue is getting their abi since currently we're getting from etherscan
- Have an "Amount minted in x minutes" (Might have to use database here, one script while:trues the contracts INTO database, another removes ones > the time)
or try using filter command in web3
- Add opensea functionality, so return links that are on their opensea, also return icon.
Maybe make like an "asset" class
- Fetch amount pending at time of data retrieval
- Organize code into functions, if name=main, documentation, all that fancy shit
- Add ability to pocketwatch a wallet address
- Switch from using while:true to webhooks

"""

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
