
import asyncio
import pathlib
import ssl
import websockets
import json
import inspect
import os
import base64
import copy
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

    # def getTreeLocal(self):
    #     if self.__bloonRootDir is None:
    #         print("[INFO] Please call getTreeDataRemote_async() first.")
    #     else:
    #         # Tree data to return
    #         treeData = {
    #             # elements are just localRelPath string of folders
    #             "all_folders_localRelPath_set": {},
    #             # element key: localRelPath string of file; element value: Tuple ==> (version:int, checksum: string)
    #             "all_files_localRelPath_dict": {}
    #         }
    #         # TODO to impl. later
    #         return treeData

    def storeTreeData(self, treeData):

        if self.__bloonRootDir is None:
            print("[INFO] Please call getTreeDataRemote_async() first.")
        else:
            os.makedirs(self.__bloonRootDir)
            
            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="all_folders_localRelPath_set") as folder_set_db:
                folder_set = treeData["all_folders_localRelPath_set"]
                for tmpKey in folder_set:
                    folder_set_db[tmpKey] = None

                folder_set_db.commit()

            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="all_files_localRelPath_dict") as files_dict_db:
                files_dict = treeData["all_files_localRelPath_dict"]
                for tmpKey in files_dict:
                    tmpVal = files_dict[tmpKey]
                    files_dict_db[tmpKey] = tmpVal

                files_dict_db.commit()

    async def getTreeDataRemote_async(self, shareID):

        # Tree data to return
        treeData = {
            # elements are just localRelPath string of folders
            "all_folders_localRelPath_set": {},
            # element key: localRelPath string of file; element value: Tuple ==> (version:int, checksum: string)
            "all_files_localRelPath_dict": {}
        }

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
                    self.__handle_bloonRootDir(root_localRelPath, treeData)
                    self.__handle_childFiles(
                        root_localRelPath, childCards, treeData)

                    for childFolder in childFolders:
                        chF_isRecycled = childFolder["isRecycled"]
                        if not chF_isRecycled:
                            chF_name = childFolder["name"]
                            chF_folderID = childFolder["folderID"]
                            chF_localRelPath = root_localRelPath + "/" + chF_name
                            await self.__getChildFolderRecursiveUnit_async(api, shareID, chF_folderID, chF_localRelPath, treeData)

            else:
                """
                It will enter this block only if item itself of this sharelink is not a folder.
                """
                # outAll = await api.getCard_async({"shareID": shareID, "cardID": itemID})
                # outData = outAll["data"]
                # print(outData)
                print("[INFO] This sharelink is not a folder.")

        return treeData

    async def __getChildFolderRecursiveUnit_async(self, api, shareID, folderID, localRelPath, treeData):

        treeData["all_folders_localRelPath_set"][localRelPath] = None

        outAll = await api.getFolder_async({"shareID": shareID, "folderID": folderID})
        outData = outAll["data"]
        isRecycled = outData["isRecycled"]
        if not isRecycled:
            # name = outData["name"] # no use for now
            childCards = outData["childCards"]
            childFolders = outData["childFolders"]

        self.__handle_childFiles(localRelPath, childCards, treeData)

        for childFolder in childFolders:
            chF_isRecycled = childFolder["isRecycled"]
            if not chF_isRecycled:
                chF_name = childFolder["name"]
                chF_folderID = childFolder["folderID"]
                chF_localRelPath = localRelPath + "/" + chF_name
                await self.__getChildFolderRecursiveUnit_async(api, shareID, chF_folderID, chF_localRelPath, treeData)

    def __handle_bloonRootDir(self, root_localRelPath, treeData):
        self.__bloonRootDir = os.path.join(
            self.WORK_DIR_ABS_PATH_STR, root_localRelPath)
        print("bloon root dir: [" + self.__bloonRootDir + "]")
        # os.makedirs(self.__bloonRootDir, exist_ok=True)

        self.__broSyncDbFileAbsPath = os.path.join(
            self.__bloonRootDir, BroSync.DB_FILE_NAME)
        print("db file: [" + self.__broSyncDbFileAbsPath + "]")
        treeData["all_folders_localRelPath_set"][root_localRelPath] = None

    def __handle_childFiles(self, localRelPath, childCards, treeData):

        for childCard in childCards:
            chC_isRecycled = childCard["isRecycled"]
            if not chC_isRecycled:
                chC_name = childCard["name"]
                chC_extension = childCard["extension"]
                chC_version = childCard["version"]  # int
                # binary in base64 format string
                chC_checksum_b64str = childCard["checksum"]
                chC_checksum_str = base64.b64decode(
                    chC_checksum_b64str).decode("UTF-8")

                chC_localRelPath = localRelPath + "/" + chC_name + "." + chC_extension

                treeData["all_files_localRelPath_dict"][chC_localRelPath] = (
                    chC_version, chC_checksum_str)


class Main:
    async def main(self):
        shareID = "JJ5RWaBV"  # test data
        # shareID = "WZys1ZoW" # test data
        workDir = "C:\\Users\\patwnag\\Desktop\\"

        bs = BroSync(workDir)

        treeData_remote = await bs.getTreeDataRemote_async(shareID)
        # print(treeData_remote)

        bs.storeTreeData(treeData_remote)

        # treeData_local = bs.getTreeLocal()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
