
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
from Ctx import Ctx


class TreeDataManager:

    WSS_CLIENT_PAYLOAD_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    DB_FILE_NAME = ".bro-sync.db"

    def __init__(self, workDir, shareID):
        self.WORK_DIR_ABS_PATH_STR = os.path.abspath(workDir)
        self.SHARE_ID = shareID

        self.__bloonRootDir = None
        self.__broSyncDbFileAbsPath = None
        self.__treeData_remote_current = None
        self.__treeData_remote_previous = None
        self.__folders_and_files_diff_list_for_action = None

        self.__apiUrl = "wss://192.168.1.198:8443/Bloon_Adjutant/api"  # test
        # self.__apiUrl = "wss://adj-xiaolongbao.bloon.io/Bloon_Adjutant/api"
        # self.__apiUrl = "wss://adj-stinky-tofu.bloon.io/Bloon_Adjutant/api"
        # self.__apiUrl = "wss://adj-bubble-tea.bloon.io/Bloon_Adjutant/api"

        self.__ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if Ctx.CLOSE_SSL_CERT_VERIFY:
            self.__ssl_context.check_hostname = False  # for test only
            self.__ssl_context.verify_mode = ssl.CERT_NONE  # for test only

    """
    ==================================================
    Simple getter/setter def. START
    ==================================================
    """

    def getWorkDir(self):
        return self.WORK_DIR_ABS_PATH_STR

    def getBloonRootDir(self):
        return self.__bloonRootDir

    def getCurrentTreeDataRemote(self):
        return self.__treeData_remote_current

    def getPreviousTreeDataRemote(self):
        """
        Return None if no data stored or any kind of err. 
        """
        return self.__treeData_remote_previous

    def getDiffForAction(self):
        """
        return a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        """
        return self.__folders_and_files_diff_list_for_action

    """
    ==================================================
    Simple getter/setter def. END
    ==================================================
    """

    def storeCurrentAsPrevious(self):
        if self.__bloonRootDir is None:
            print("[INFO] Please call retrieveCurrentTreeDataRemote_async() first.")
        else:
            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="ctx") as ctx_db:
                ctx_db.clear()
                ctx = self.__treeData_remote_current["ctx"]
                for tmpKey in ctx:
                    tmpVal = ctx[tmpKey]
                    ctx_db[tmpKey] = tmpVal
                ctx_db.commit()

            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="folder_set") as folder_set_db:
                folder_set_db.clear()
                folder_set = self.__treeData_remote_current["folder_set"]
                for tmpKey in folder_set:
                    folder_set_db[tmpKey] = None
                folder_set_db.commit()

            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="file_dict") as file_dict_db:
                file_dict_db.clear()
                file_dict = self.__treeData_remote_current["file_dict"]
                for tmpKey in file_dict:
                    tmpVal = file_dict[tmpKey]
                    file_dict_db[tmpKey] = tmpVal
                file_dict_db.commit()

    def createDiffListForAction(self):
        folder_paths_need_to_make = []
        file_paths_need_to_download = []

        # --------------------------------------------------
        # for folders
        # --------------------------------------------------
        folder_set__current = self.__treeData_remote_current["folder_set"]
        folder_set__previous = {} if self.__treeData_remote_previous is None else self.__treeData_remote_previous["folder_set"]

        # all new file path need to download
        deff_folder_set = folder_set__current.keys() - folder_set__previous.keys()
        folder_paths_need_to_make.extend(deff_folder_set)

        # --------------------------------------------------
        # for files
        # --------------------------------------------------
        file_dict__current = self.__treeData_remote_current["file_dict"]
        file_dict__previous = {} if self.__treeData_remote_previous is None else self.__treeData_remote_previous["file_dict"]

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

        self.__folders_and_files_diff_list_for_action = (folder_paths_need_to_make, file_paths_need_to_download)

    def loadPreviousTreeDataRemote(self):
        if self.__bloonRootDir is None:
            print("[INFO] Please call retrieveCurrentTreeDataRemote_async() first.")
        else:
            if not os.path.exists(self.__broSyncDbFileAbsPath):
                return None

            treeData = {}

            with SqliteDict(self.__broSyncDbFileAbsPath, tablename="ctx") as ctx_db:
                ctx_mem = {}
                for tmpKey in ctx_db:
                    tmpVal = ctx_db[tmpKey]
                    ctx_mem[tmpKey] = tmpVal
                treeData["ctx"] = ctx_mem

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

            self.__treeData_remote_previous = treeData

    async def retrieveCurrentTreeDataRemote_async(self):

        # Tree data to return
        treeData = {
            "ctx": {
                "bloon_name": None
            },
            # elements are just localRelPath string of folders
            "folder_set": {},
            # element key: localRelPath string of file; element value: Tuple ==> (version:int, checksum: string)
            "file_dict": {}
        }

        async with websockets.connect(self.__apiUrl, ssl=self.__ssl_context, max_size=TreeDataManager.WSS_CLIENT_PAYLOAD_MAX_SIZE) as wss:
            api = WssApiCaller(wss)
            outData = await api.getShareInfo_async({"shareID": self.SHARE_ID})
            shareData = outData["data"]["shareData"]
            itemID = shareData["itemID"]
            isFolder = shareData["isFolder"]

            if isFolder:
                outAll = await api.getFolder_async({"shareID": self.SHARE_ID, "folderID": itemID})
                outData = outAll["data"]

                isRecycled = outData["isRecycled"]
                if not isRecycled:
                    # folderID = outData["folderID"] # it should be the same as "itemID"
                    name = outData["name"]
                    childCards = outData["childCards"]
                    childFolders = outData["childFolders"]

                    treeData["ctx"]["bloon_name"] = name
                    root_localRelPath = name
                    treeData["folder_set"][root_localRelPath] = None

                    self.__bloonRootDir = os.path.join(self.WORK_DIR_ABS_PATH_STR, root_localRelPath)
                    print("[DEBUG] __bloonRootDir: [" + self.__bloonRootDir + "]")

                    self.__broSyncDbFileAbsPath = os.path.join(self.WORK_DIR_ABS_PATH_STR, TreeDataManager.DB_FILE_NAME)
                    print("[DEBUG] __broSyncDbFileAbsPath: [" + self.__broSyncDbFileAbsPath + "]")

                    self.__handle_childFiles(root_localRelPath, childCards, treeData)

                    for childFolder in childFolders:
                        chF_isRecycled = childFolder["isRecycled"]
                        if not chF_isRecycled:
                            chF_name = childFolder["name"]
                            chF_folderID = childFolder["folderID"]
                            chF_localRelPath = root_localRelPath + "/" + chF_name
                            await self.__getChildFolderRecursiveUnit_async(api, self.SHARE_ID, chF_folderID, chF_localRelPath, treeData)

            else:
                """
                It will enter this block only if item itself of this sharelink is not a folder.
                """
                # outAll = await api.getCard_async({"shareID": shareID, "cardID": itemID})
                # outData = outAll["data"]
                # print(outData)
                print("[INFO] This sharelink is not a folder.")

        self.__treeData_remote_current = treeData

    @staticmethod
    async def __getChildFolderRecursiveUnit_async(api, shareID, folderID, localRelPath, treeData):

        treeData["folder_set"][localRelPath] = None

        outAll = await api.getFolder_async({"shareID": shareID, "folderID": folderID})
        outData = outAll["data"]
        isRecycled = outData["isRecycled"]
        if not isRecycled:
            # name = outData["name"] # no use for now
            childCards = outData["childCards"]
            childFolders = outData["childFolders"]

        TreeDataManager.__handle_childFiles(localRelPath, childCards, treeData)

        for childFolder in childFolders:
            chF_isRecycled = childFolder["isRecycled"]
            if not chF_isRecycled:
                chF_name = childFolder["name"]
                chF_folderID = childFolder["folderID"]
                chF_localRelPath = localRelPath + "/" + chF_name
                await TreeDataManager.__getChildFolderRecursiveUnit_async(api, shareID, chF_folderID, chF_localRelPath, treeData)

    @staticmethod
    def __handle_childFiles(localRelPath, childCards, treeData):

        for childCard in childCards:
            chC_isRecycled = childCard["isRecycled"]
            if not chC_isRecycled:
                chC_name = childCard["name"]
                chC_extension = childCard["extension"]
                chC_version = childCard["version"]  # int
                chC_checksum_b64str = childCard["checksum"]  # binary in base64 format string
                chC_checksum_str = base64.b64decode(chC_checksum_b64str).decode("UTF-8")

                chC_localRelPath = localRelPath + "/" + chC_name + "." + chC_extension

                treeData["file_dict"][chC_localRelPath] = (chC_version, chC_checksum_str)
