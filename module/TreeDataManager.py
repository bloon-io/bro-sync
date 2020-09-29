
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


class TreeDataManager:

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

    def storeTreeDataRemote(self, treeData):
        if self.__bloonRootDir is None:
            print("[INFO] Please call getTreeDataRemote_async() first.")
        else:
            os.makedirs(self.__bloonRootDir, exist_ok=True)
            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="folder_set") as folder_set_db:
                folder_set = treeData["folder_set"]
                for tmpKey in folder_set:
                    folder_set_db[tmpKey] = None

                folder_set_db.commit()

            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="file_dict") as file_dict_db:
                file_dict = treeData["file_dict"]
                for tmpKey in file_dict:
                    tmpVal = file_dict[tmpKey]
                    file_dict_db[tmpKey] = tmpVal

                file_dict_db.commit()

    def createDiffListForAction(self, treeData_remote_current, treeData_remote_previous):
        """
        return a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        """
        folder_paths_need_to_make = []
        file_paths_need_to_download = []

        # --------------------------------------------------
        # for folders
        # --------------------------------------------------
        folder_set__current = treeData_remote_current["folder_set"]
        folder_set__previous = {
        } if treeData_remote_previous is None else treeData_remote_previous["folder_set"]

        # all new file path need to download
        deff_folder_set = folder_set__current.keys() - folder_set__previous.keys()
        folder_paths_need_to_make.extend(deff_folder_set)

        # --------------------------------------------------
        # for files
        # --------------------------------------------------
        file_dict__current = treeData_remote_current["file_dict"]
        file_dict__previous = {
        } if treeData_remote_previous is None else treeData_remote_previous["file_dict"]

        # all new file path need to download
        deff_file_set = file_dict__current.keys() - file_dict__previous.keys()
        file_paths_need_to_download.extend(deff_file_set)

        # all intersection file path need to compare version
        inter_set = file_dict__current.keys() & file_dict__previous.keys()
        for tmpPath in inter_set:
            v__current = file_dict__current[tmpPath][0]
            v__previous = file_dict__previous[tmpPath][0]
            if v__current > v__previous:
                file_paths_need_to_download.append(tmpPath)

        # print("folder_paths_need_to_make: " + str(folder_paths_need_to_make))
        # print("file_paths_need_to_download: " + str(file_paths_need_to_download))
        return (folder_paths_need_to_make, file_paths_need_to_download)

    def loadTreeDataRemote(self):
        """
        Return None if no data stored or any kind of err. 
        """
        if self.__bloonRootDir is None:
            print("[INFO] Please call getTreeDataRemote_async() first.")
        else:
            if (not os.path.exists(self.__bloonRootDir)) or (not os.path.exists(self.__broSyncDbFileAbsPath)):
                return None

            treeData = {}

            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="folder_set") as folder_set_db:
                folder_set_mem = {}
                for tmpKey in folder_set_db:
                    folder_set_mem[tmpKey] = None
                treeData["folder_set"] = folder_set_mem

            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="file_dict") as file_dict_db:
                file_dict_mem = {}
                for tmpKey in file_dict_db:
                    tmpVal = file_dict_db[tmpKey]
                    file_dict_mem[tmpKey] = tmpVal
                treeData["file_dict"] = file_dict_mem

            return treeData

    async def getTreeDataRemote_async(self, shareID):

        # Tree data to return
        treeData = {
            # elements are just localRelPath string of folders
            "folder_set": {},
            # element key: localRelPath string of file; element value: Tuple ==> (version:int, checksum: string)
            "file_dict": {}
        }

        async with websockets.connect(self.__apiUrl, ssl=self.__ssl_context, max_size=TreeDataManager.WSS_CLIENT_PAYLOAD_MAX_SIZE) as wss:
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

        treeData["folder_set"][localRelPath] = None

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
        print("[DEBUG] bloon root dir: [" + self.__bloonRootDir + "]")
        # os.makedirs(self.__bloonRootDir, exist_ok=True)

        self.__broSyncDbFileAbsPath = os.path.join(
            self.__bloonRootDir, TreeDataManager.DB_FILE_NAME)
        print("[DEBUG] db file: [" + self.__broSyncDbFileAbsPath + "]")
        treeData["folder_set"][root_localRelPath] = None

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

                treeData["file_dict"][chC_localRelPath] = (
                    chC_version, chC_checksum_str)


class Main:
    async def main(self):
        shareID = "JJ5RWaBV"  # test data
        # shareID = "WZys1ZoW" # test data
        workDir = "C:\\Users\\patwnag\\Desktop\\"
        tdm = TreeDataManager(workDir)

        # --------------------------------------------------
        treeData_remote_current = await tdm.getTreeDataRemote_async(shareID)
        # print(treeData_remote_current)
        # print("----------")

        # --------------------------------------------------
        treeData_remote_previous = tdm.loadTreeDataRemote()
        # print(treeData_remote_previous)
        # print("----------")

        # --------------------------------------------------
        diffListTuple = tdm.createDiffListForAction(
            treeData_remote_current, treeData_remote_previous)
        print(diffListTuple)

        tdm.storeTreeDataRemote(treeData_remote_current)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
