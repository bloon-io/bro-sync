
import asyncio
import pathlib
import ssl
import websockets
import json
import inspect
from WssApiCaller import WssApiCaller

class BroSync:

    def __init__(self):
        self.__ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.__ssl_context.check_hostname = False  # for test only
        self.__ssl_context.verify_mode = ssl.CERT_NONE  # for test only

        self.__apiUrl = "wss://192.168.1.198:8443/Bloon_Adjutant/api"  # test
        # self.__apiUrl = "wss://adj-xiaolongbao.bloon.io/Bloon_Adjutant/api"
        # self.__apiUrl = "wss://adj-stinky-tofu.bloon.io/Bloon_Adjutant/api"
        # self.__apiUrl = "wss://adj-bubble-tea.bloon.io/Bloon_Adjutant/api"

    async def getTree(self, shareID):
        async with websockets.connect(self.__apiUrl, ssl=self.__ssl_context) as wss:
            api = WssApiCaller(wss)
            outData = await api.getShareInfo_async({"token": None, "shareID": shareID})
            shareData = outData["data"]["shareData"]
            itemID = shareData["itemID"]
            isFolder = shareData["isFolder"]

            if isFolder:
                outData = await api.getFolder_async({"token": None, "shareID": shareID, "folderID": itemID})
                print(outData)
            else:
                pass


class Main:
    async def main(self):
        shareID = "JJ5RWaBV"  # test data
        # shareID = "WZys1ZoW" # test data

        bs = BroSync()
        await bs.getTree(shareID)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
