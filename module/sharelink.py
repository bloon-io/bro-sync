
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
            outData = await api.getShareInfo_async({"shareID": shareID})
            shareData = outData["data"]["shareData"]
            itemID = shareData["itemID"]
            isFolder = shareData["isFolder"]

            if isFolder:
                outAll = await api.getFolder_async({"shareID": shareID, "folderID": itemID})
                outData = outAll["data"]

                isRecycled = outData["isRecycled"]
                if not isRecycled:
                    folderID = outData["folderID"] # it should be the same as "itemID"

                    name = outData["name"]
                    modifyTime = outData["modifyTime"] # TODO [?] need to be persistent, used in the future
                    childCards = outData["childCards"]
                    childFolders = outData["childFolders"]

                    for childCard in childCards:
                        chC_isRecycled = childCard["isRecycled"]
                        if not chC_isRecycled:
                            chC_name = childCard["name"]
                            chC_extension = childCard["extension"]
                            chC_version = childCard["version"]  # int # TODO need to be persistent, used in the future
                            chC_checksum = childCard["checksum"] # binary in base64 format string # TODO need to be persistent, used in the future
                            
                            chC_finalLocalRelPath = "/" + name + "/" + chC_name + "." + chC_extension
                            print(chC_finalLocalRelPath)
                            # TODO to store all chC_finalLocalRelPath

                    for childFolder in childFolders:
                        chF_isRecycled = childFolder["isRecycled"]
                        if not chF_isRecycled:
                            chF_name = childFolder["name"]
                            chF_finalLocalRelPath = "/" + name + "/" + chF_name
                            print(chF_finalLocalRelPath)
                            # TODO to store all chF_finalLocalRelPath
                            # TODO to make recursive func. call

            else:
                """
                It will enter this block if only sharelink itself is not a folder.
                """
                # outAll = await api.getCard_async({"shareID": shareID, "cardID": itemID})
                # outData = outAll["data"]
                # print(outData)
                print("[INFO] This sharelink is not a folder.")


class Main:
    async def main(self):
        shareID = "JJ5RWaBV"  # test data
        # shareID = "WZys1ZoW" # test data

        bs = BroSync()
        await bs.getTree(shareID)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
