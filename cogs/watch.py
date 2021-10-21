"""TODO
- Add proper documentation for each function and class (Use google's styling)
- Implement !help command
"""

import json
import asyncio
import discord
import websockets
from discord.ext import commands
from __main__ import watch

def format_embed(dict):
    """Formats embed for watching output

    Arguments:
        Formatted dictionary for output

    Returns:
        Discord embed object
    """

    contract_info = watch.get_contract_info(dict['to'])
    watchlist = watch.get_watchlist()
    value_text = watch.wei_to_ether(dict["value"])
    if dict['status'] == 'confirmed':
        value_text += f' ETH\n{dict["gasPriceGwei"]} Gwei'

    alias = ''
    for alias_i in watchlist:
        if dict['watchedAddress'] in watchlist[alias_i]['addresses']:
            alias = alias_i

    embed = discord.Embed(
        title=contract_info['name'],
        description=f'[Contract](https://etherscan.io/address/{dict["to"]})\n \
        [Transaction](https://etherscan.io/tx/{dict["hash"]})\n \
        [Opensea]({contract_info["opensea_site"]})\n \
        [Website]({contract_info["website"]})\n \
        [Discord]({contract_info["discord"]})',
        color=discord.Color.blurple()
        )
    embed.add_field(name='Value', value=value_text)
    embed.set_author(name=alias, icon_url=watchlist[alias]['image_url'])
    embed.set_thumbnail(url=contract_info["image_url"])
    embed.set_footer(text=dict['status'])

    return embed

class Watch(commands.Cog):

    @commands.command(name='watchlist', aliases=['wl'])
    async def get_watchlist(self, ctx):
        embed = discord.Embed(
            title='Watchlist',
            color=discord.Color.dark_teal()
        )

        watchlist = watch.get_watchlist()
        for alias in watchlist:
            for address in watchlist[alias]['addresses']:
                embed.add_field(name=alias, value=f'[Etherscan](https://etherscan.io/address/{address})\n[Opensea](https://opensea.io/{address})')

        await ctx.reply(embed=embed)

    @commands.command(name='add')
    async def add_watchlist(self, ctx):
        args = ctx.message.content.split(' ')[1:]
        if len(args) < 2:
            await ctx.reply(embed=discord.Embed(title='Wrong syntax!\nUse the help command'), delete_after=5)
            return

        alias, address = args[0], args[1]
        result = watch.add_address_to_watchlist(alias, address) if len(args) == 2 else watch.add_address_to_watchlist(alias, address, args[2])

        if result == 0:
            embed = discord.Embed(title='Address already in watchlist!', color=discord.Color.red())
        elif result == -1:
            embed = discord.Embed(title='Invalid address!', color=discord.Color.red(), delete_after=5) 
        else:
            embed = discord.Embed(title='Added address to watchlist', color=discord.Color.green())
            embed.add_field(name='Alias', value=alias)
            embed.add_field(name='Address', value=address)

        await ctx.reply(embed=embed, delete_after=5)

    @commands.command(name='remove')
    async def remove_watchlist(self, ctx):
        args = ctx.message.content.split(' ')[1:]
        if len(args) < 1:
            await ctx.reply(embed=discord.Embed(title='Wrong syntax!\nUse the help command'), delete_after=5)
            return

        alias = args[0]
        result = watch.remove_address_from_watchlist(alias) if len(args) == 1 else watch.remove_address_from_watchlist(alias, args[1])

        if result == 0:
            embed = discord.Embed(title='Alias/Address not in watchlist!', color=discord.Color.red())
        else:
            embed = discord.Embed(title='Removed alias/address from watchlist',color=discord.Color.green())
            embed.add_field(name='Alias', value=alias)
            if len(args) > 1:
                embed.add_field(name='Address', value=args[1])

        await ctx.reply(embed=embed, delete_after=5)

    @commands.command(name='clear')
    async def clear_watchlist(self, ctx):
        watch.clear_watchlist()
        await ctx.reply(embed=discord.Embed(title='Cleared Watchlist!'), delete_after=5)

    @commands.command(name='changepfp', aliases=['newpfp', 'setpfp'])
    async def change_pfp(self, ctx):
        args = ctx.message.content.split(' ')[1:]
        if len(args) < 2:
            await ctx.reply(embed=discord.Embed(title='Wrong syntax!\nUse the help command'), delete_after=5)
            return

        alias, image_url = args[0], args[1]
        result = watch.change_pfp(alias, image_url)

        if result == -1:
            embed = discord.Embed(title='Alias does not exist!', color=discord.Color.red())
        elif result == 0:
            embed = discord.Embed(title='URL is invalid! Make sure its a regular image format (JPEG, PNG, etc)', color=discord.Color.red())
        else:
            embed = discord.Embed(title=f'Changed picture for {alias}', color=discord.Color.green())
        
        await ctx.reply(embed=embed, delete_after=5)

    @commands.command(name='getpfp', aliases=['pfp'])
    async def get_pfp(self, ctx):
        args = ctx.message.content.split(' ')[1:]
        if len(args) < 1:
            await ctx.reply(embed=discord.Embed(title='Wrong syntax!\nUse the help command'), delete_after=5)
            return

        alias = args[0]
        result = watch.get_pfp(alias)

        if result == -1:
            embed = discord.Embed(title='Alias does not exist!', color=discord.Color.red())
        else:
            embed = discord.Embed(color=discord.Color.green())
            embed.set_image(url=result)
        
        await ctx.reply(embed=embed, delete_after=5)

    @commands.command(name='watching')
    async def is_watching(self, ctx):
        if watch.is_watching():
            embed = discord.Embed(title='Watching!', color=discord.Color.green())
        else:
            embed = discord.Embed(title='Not Watching!', color=discord.Color.red())

        await ctx.reply(embed=embed, delete_after=5)

    @commands.command(name='start', aliases=['watch'])
    async def start_watching(self, ctx):

        if watch.is_watching():
            await ctx.reply(embed=discord.Embed(title='Already running!', color=discord.Color.red()), delete_after=5)
            return

        watchlist = watch.get_watchlist()
        watch.watching = True
        url = 'wss://api.blocknative.com/v0'
        async with websockets.connect(url) as ws:
            await ws.recv()
            await watch.verify_api(ws)
            for alias in watchlist:
                for address in watchlist[alias]['addresses']:
                    await watch.subscribe_address(ws, address)
                    await asyncio.sleep(1)

            await ctx.reply(embed=discord.Embed(title='Started!', color=discord.Color.gold()))

            while watch.is_watching():
                result = await ws.recv()
                result_json = json.loads(result)['event']['transaction']
                filtered_json = dict()

                filtered_keys = ['watchedAddress', 'status', 'hash', 'from', 'to', 'value', 'gasPriceGwei']
                for key in result_json:
                    if key in filtered_keys:
                        filtered_json[key] = result_json[key]

                # Checks if transaction is being sent FROM our watchlist address (i.e. mint)
                if filtered_json['from'].lower() == filtered_json['watchedAddress'].lower():
                    await ctx.send(embed=format_embed(filtered_json))

            print('Stopped watching')

    @commands.command(name='test_embed')
    async def test(self, ctx):
        result = {
            "status": "confirmed",
            "network": "main",
            "blocksPending": 2,
            "pendingTimeStamp": "2021-10-19T18:17:01.492Z",
            "pendingBlockNumber": 13449739,
            "hash": "0x78834579a1da0f0e9614551657bc758fce983dea61f30a57e2dc966f0b50a306",
            "from": "0xe11a50e299121db7849cb28604917Cd615dc1BCC",
            "to": "0x4BE3223f8708Ca6b30D1E8b8926cF281EC83E770",
            "value": "0",
            "gas": 107849,
            "blockHash": "0xe45ab1ccb003b28f9208f3f954d4c16e634b9497796732af8e29cd50763ebc01",
            "blockNumber": 13449741,
            "input": "0x23b872dd...",
            "gasPrice": "79546611930",
            "gasPriceGwei": 80,
            "contractCall": {
                "contractType": "erc721",
                "methodName": "transferFrom",
                "params": {
                "_from": "0xe11a50e299121db7849cb28604917Cd615dc1BCC",
                "_to": "0x102c412bc7Cf8276CCCb9fD5A2e5fc12125C1bbb",
                "_tokenId": "3109"
                },
                "contractName": "PartyDegenerates"
            },
            "gasUsed": "98249",
            "type": 2,
            "maxFeePerGas": "100627610412",
            "maxPriorityFeePerGas": "2000000000",
            "baseFeePerGas": "77546611930",
            "asset": "PARTY",
            "blockTimeStamp": "2021-10-19T18:17:03.000Z",
            "watchedAddress": "0xe11a50e299121db7849cb28604917cd615dc1bcc",
            "direction": "outgoing",
            "counterparty": "0x102c412bc7Cf8276CCCb9fD5A2e5fc12125C1bbb",
            "apiKey": "d67a78ff-96a5-4d8b-b9f2-e110dd73433f",
            "dispatchTimestamp": "2021-10-19T18:17:04.974Z"
        }

        result_json = result
        new_json = dict()

        filtered_keys = ['watchedAddress', 'status', 'hash', 'from', 'to', 'value', 'gasPriceGwei']
        for key in result_json:
            if key in filtered_keys:
                new_json[key] = result_json[key]

        # Checks if transaction is being sent from our watchlist address
        if new_json['from'].lower() == new_json['watchedAddress'].lower():
            await ctx.send(embed=format_embed(new_json))

    @commands.command(name='stop')
    async def stop_watching(self, ctx):
        watch.stop_watching()
        await ctx.reply(embed=discord.Embed(title='Will stop watching after next notification'), delete_after=5)

def setup(bot):
    bot.add_cog(Watch(bot))