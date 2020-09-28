
import asyncio
import pathlib
import ssl
import websockets
import json
import inspect
import os
from WssApiCaller import WssApiCaller
from sqlitedict import SqliteDict


class BroSync:

    WSS_CLIENT_PAYLOAD_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    DB_FILE_NAME = ".bro-sync.db"

    def __init__(self, workDir):
        self.WORK_DIR_ABS_PATH_STR = os.path.abspath(workDir)
        self.__bloonRootDir = None
        self.__broSyncDbFileAbsPath = None

        self.__apiUrl = "wss://192.168.1.198:8443/Bloon_Adjutant/api"  # test
        # self.__apiUrl = "wss://adj-xiaolongbao.bloon.io/Bloon_Adjutant/api"
        # self.__apiUrl = "wss://adj-stinky-tofu.bloon.io/Bloon_Adjutant/api"
        # self.__apiUrl = "wss://adj-bubble-tea.bloon.io/Bloon_Adjutant/api"

        self.__ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.__ssl_context.check_hostname = False  # for test only
        self.__ssl_context.verify_mode = ssl.CERT_NONE  # for test only

    async def __getChildFolderRecursiveUnit_async(self, api, shareID, folderID, localRelPath):

        with self.__getFoldersDict() as dbDict:
            dbDict[localRelPath] = None
            dbDict.commit()

        outAll = await api.getFolder_async({"shareID": shareID, "folderID": folderID})
        outData = outAll["data"]
        isRecycled = outData["isRecycled"]
        if not isRecycled:
            # name = outData["name"] # no use for now
            childCards = outData["childCards"]
            childFolders = outData["childFolders"]

        self.__handle_childFiles(localRelPath, childCards)

        for childFolder in childFolders:
            chF_isRecycled = childFolder["isRecycled"]
            if not chF_isRecycled:
                chF_name = childFolder["name"]
                chF_folderID = childFolder["folderID"]
                chF_localRelPath = localRelPath + "/" + chF_name
                await self.__getChildFolderRecursiveUnit_async(api, shareID, chF_folderID, chF_localRelPath)

    def __handle_bloonRootDir(self, root_localRelPath):
        self.__bloonRootDir = os.path.join(
            self.WORK_DIR_ABS_PATH_STR, root_localRelPath)
        print("bloon root dir: [" + self.__bloonRootDir + "]")
        os.makedirs(self.__bloonRootDir, exist_ok=True)

        self.__broSyncDbFileAbsPath = os.path.join(
            self.__bloonRootDir, BroSync.DB_FILE_NAME)
        print("db file: [" + self.__broSyncDbFileAbsPath + "]")
        with self.__getFoldersDict() as dbDict:
            dbDict[root_localRelPath] = None
            dbDict.commit()

    def __handle_childFiles(self, localRelPath, childCards):
        with self.__getFilesDict() as dbDict:
            for childCard in childCards:
                chC_isRecycled = childCard["isRecycled"]
                if not chC_isRecycled:
                    chC_name = childCard["name"]
                    chC_extension = childCard["extension"]
                    chC_version = childCard["version"]  # int
                    # binary in base64 format string
                    chC_checksum_b64str = childCard["checksum"]

                    chC_localRelPath = localRelPath + "/" + chC_name + "." + chC_extension

                    dbDict[chC_localRelPath] = (
                        chC_version, chC_checksum_b64str)
            dbDict.commit()

    async def getTree_async(self, shareID):

        async with websockets.connect(self.__apiUrl, ssl=self.__ssl_context, max_size=BroSync.WSS_CLIENT_PAYLOAD_MAX_SIZE) as wss:
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
                    # folderID = outData["folderID"] # it should be the same as "itemID"
                    name = outData["name"]
                    childCards = outData["childCards"]
                    childFolders = outData["childFolders"]

                    root_localRelPath = name
                    self.__handle_bloonRootDir(root_localRelPath)
                    self.__handle_childFiles(root_localRelPath, childCards)

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

    def __getFoldersDict(self):
        # elements are just localRelPath string of folders
        return SqliteDict(self.__broSyncDbFileAbsPath, tablename="all_folders_localRelPath_set")

    def __getFilesDict(self):
        # element key: localRelPath string of file; element value: Tuple ==> (version:int, checksum:base64 string)
        return SqliteDict(self.__broSyncDbFileAbsPath, tablename="all_files_localRelPath_dict")


class Main:
    async def main(self):
        shareID = "JJ5RWaBV"  # test data
        # shareID = "WZys1ZoW" # test data
        workDir = "C:\\Users\\patwnag\\Desktop\\"

        bs = BroSync(workDir)
        await bs.getTree_async(shareID)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
