
import asyncio
import pathlib
import ssl
import websockets
import json
import inspect
from WssApiCaller import WssApiCaller


class BroSync:

    WSS_CLIENT_PAYLOAD_MAX_SIZE = 10 * 1024 * 1024 # 10MB

    def __init__(self):
        self.__ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.__ssl_context.check_hostname = False  # for test only
        self.__ssl_context.verify_mode = ssl.CERT_NONE  # for test only

        self.__apiUrl = "wss://192.168.1.198:8443/Bloon_Adjutant/api"  # test
        # self.__apiUrl = "wss://adj-xiaolongbao.bloon.io/Bloon_Adjutant/api"
        # self.__apiUrl = "wss://adj-stinky-tofu.bloon.io/Bloon_Adjutant/api"
        # self.__apiUrl = "wss://adj-bubble-tea.bloon.io/Bloon_Adjutant/api"

    async def __getChildFolderRecursiveUnit_async(self, api, shareID, folderID, localRelPath):
        print(localRelPath)
        outAll = await api.getFolder_async({"shareID": shareID, "folderID": folderID})
        outData = outAll["data"]
        isRecycled = outData["isRecycled"]
        if not isRecycled:
            name = outData["name"]
            childCards = outData["childCards"]
            childFolders = outData["childFolders"]

        for childCard in childCards:
            chC_isRecycled = childCard["isRecycled"]
            if not chC_isRecycled:
                chC_name = childCard["name"]
                chC_extension = childCard["extension"]
                chC_version = childCard["version"]  # int
                chC_checksum = childCard["checksum"] # binary in base64 format string
                
                chC_localRelPath = localRelPath + "/" + chC_name + "." + chC_extension
                # TODO to store chC_version, chC_checksum
                print(chC_localRelPath)
                
        for childFolder in childFolders:
            chF_isRecycled = childFolder["isRecycled"]
            if not chF_isRecycled:
                chF_name = childFolder["name"]
                chF_folderID = childFolder["folderID"]
                chF_localRelPath = localRelPath + "/" + chF_name
                await self.__getChildFolderRecursiveUnit_async(api, shareID, chF_folderID, chF_localRelPath)

    async def getTree_async(self, shareID):
        async with websockets.connect(self.__apiUrl, ssl=self.__ssl_context, max_size= BroSync.WSS_CLIENT_PAYLOAD_MAX_SIZE) as wss:
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
                    childCards = outData["childCards"]
                    childFolders = outData["childFolders"]

                    root_localRelPath = "/" + name
                    print(root_localRelPath)

                    for childCard in childCards:
                        chC_isRecycled = childCard["isRecycled"]
                        if not chC_isRecycled:
                            chC_name = childCard["name"]
                            chC_extension = childCard["extension"]
                            chC_version = childCard["version"]  # int
                            chC_checksum = childCard["checksum"] # binary in base64 format string
                            
                            chC_localRelPath = root_localRelPath + "/" + chC_name + "." + chC_extension
                            # TODO to store chC_version, chC_checksum
                            print(chC_localRelPath)
                            
                    for childFolder in childFolders:
                        chF_isRecycled = childFolder["isRecycled"]
                        if not chF_isRecycled:
                            chF_name = childFolder["name"]
                            chF_folderID = childFolder["folderID"]
                            chF_localRelPath = root_localRelPath + "/" + chF_name
                            await self.__getChildFolderRecursiveUnit_async(api, shareID, chF_folderID, chF_localRelPath)

            else:
                """
                It will enter this block only if item itself of this sharelink is not a folder.
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
        await bs.getTree_async(shareID)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
