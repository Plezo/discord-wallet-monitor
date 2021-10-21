"""
TODO
- Add proper documentation for class and each function (Use google's styling)
- Work on edge-cases
- Allow making changes to json while listening for transactions
- Figure out why stop() isnt stopping instantly (probably cuz of all the async functions)
- Create new json if watchlist.json doesnt exist
"""

import requests
import websockets
import asyncio
import json
import datetime
from web3 import Web3
from config import *

class Watchlist:

    def __init__(self):
        self.watchlist = dict()
        self.watching = False
        self.refresh_watchlist()
    
    def get_contract_info(self, address: str):
        url = f"https://api.opensea.io/api/v1/asset_contract/{address}"

        response = requests.request('GET', url)
        contract_json = json.loads(response.text)

        if contract_json['collection'] == None:
            formatted_dict = {
                'address':      'N/A',
                'name':         'N/A',
                'description':  'N/A',
                'image_url':    'https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png',
                'opensea_site': 'N/A',
                'website':      'N/A',
                'discord':      'N/A',
                'twitter':      'N/A',
                'instagram':    'N/A',
            }
        else:
            formatted_dict = {
                'address':      address,
                'name':         contract_json['collection']['name'],
                'description':  contract_json['collection']['description'],
                'image_url':    contract_json['collection']['image_url'],
                'opensea_site': f'https://opensea.io/collection/{contract_json["collection"]["slug"]}',
                'website':      contract_json['collection']['external_url'],
                'discord':      contract_json['collection']['discord_url'],
                'twitter':      contract_json['collection']['twitter_username'],
                'instagram':    contract_json['collection']['instagram_username'],
            }

        return formatted_dict

    def is_valid_address(self, address: str):
        return Web3.isAddress(address)

    def change_pfp(self, alias: str, image_url: str):
        if alias not in self.watchlist:
            return -1
        elif image_url.split('.')[-1].lower() not in ['jpg', 'png', 'bmp', 'gif']:
            return 0
        else:
            self.watchlist[alias]['image_url'] = image_url
        
        self.save_wl()

    def get_pfp(self, alias: str):
        if alias not in self.watchlist:
            return -1
        else:
            return self.watchlist[alias]['image_url']

    def remove_address_from_watchlist(self, alias: str, address=''):
        """Removes address from watchlist
        """

        address = address.lower()
        if alias in self.watchlist and address in self.watchlist[alias]['addresses']:
            self.watchlist[alias]['addresses'].remove(address)
        elif alias in self.watchlist:
            del self.watchlist[alias]
        else:
            return 0

        self.save_wl()

    def add_address_to_watchlist(self, alias: str, address: str, image_url='https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png'):
        """Adds address to watchlist
        """
        address = address.lower()

        if image_url.split('.')[-1].lower() not in ['jpg', 'png', 'bmp', 'gif']:
            image_url = 'https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png'

        if not self.is_valid_address(address):
            return -1
        elif alias not in self.watchlist:
            self.watchlist[alias] = {'addresses': [address], 'image_url': image_url}
        elif address not in self.watchlist[alias]['addresses']:
            self.watchlist[alias]['addresses'].append(address)
            self.watchlist[alias]['image_url'] = image_url
        else:
            return 0

        self.save_wl()

    def refresh_watchlist(self):
        """Fills watchlist list from json
        """

        with open('watchlist.json') as json_file:
            self.watchlist = json.load(json_file)

    def get_watchlist(self):
        return self.watchlist

    def is_watching(self):
        return self.watching

    def save_wl(self):
        with open('watchlist.json', 'w') as json_file:
            json.dump(self.watchlist, json_file)
        
    def clear_watchlist(self):
        self.watchlist.clear()
        self.save_wl()
        print('Cleared watchlist.')

    def stop_watching(self):
        self.watching = False

    def wei_to_ether(self, amount):
        return amount / 1000000000000000000

    """ For now this is implemented in the watch.py discord command,
    that is a temporary solution (that will probably end up being permanent tbh)

    async def watch(self):
        self.watching = True
        url = 'wss://api.blocknative.com/v0'
        async with websockets.connect(url) as ws:
            await ws.recv()
            await self.verify_api(ws)
            for address in self.watchlist:
                await self.subscribe_address(ws, address)
                await asyncio.sleep(1)

            while self.watching:
                result = await ws.recv()
                result_json = json.loads(result)['event']['transaction']

                new_json = {
                    'address':          result_json['watchedAddress'],
                    'tx_hash':          result_json['hash'],
                    'from':             result_json['from'],
                    'to':               result_json['to'],
                    'value':            f'{self.wei_to_ether(int(result_json["value"]))} ETH',
                    # 'gasPriceGwei':     result_json['gasPriceGwei'],
                    'pendingTimestamp': result_json['pendingTimeStamp']
                }
            print('Stopped watching')
    """

    async def verify_api(self, ws):
        message = {
                'timeStamp': str(datetime.datetime.now()),
                'dappId': BLOCKNATIVE_API_KEY,
                'version': '1',
                'blockchain': {
                    'system': 'ethereum',
                    'network': 'main'
                },
                'categoryCode': 'initialize',
                'eventCode': 'checkDappId'
            }
        
        await ws.send(json.dumps(message))
        await ws.recv()

    async def subscribe_address(self, ws, address):
        message = {
                'timeStamp': str(datetime.datetime.now()),
                'dappId': BLOCKNATIVE_API_KEY,
                'version': '1',
                'blockchain': {
                    'system': 'ethereum',
                    'network': 'main'
                },
                'categoryCode': 'accountAddress',
                'eventCode': 'watch',
                'account': {
                    'address': address
                }
            }
    
        await ws.send(json.dumps(message))
        await ws.recv()
        print(f"Subscribed to: {address}")

    async def unsubscribe_address(self, ws, address):
        message = {
                'timeStamp': str(datetime.datetime.now()),
                'dappId': BLOCKNATIVE_API_KEY,
                'version': '1',
                'blockchain': {
                    'system': 'ethereum',
                    'network': 'main'
                },
                'categoryCode': 'accountAddress',
                'eventCode': 'unwatch',
                'account': {
                    'address': address
                }
            }

        await ws.send(json.dumps(message))