
import asyncio
import pathlib
import ssl
import websockets
import json
import inspect
import os
import base64
import copy
import logging
from sqlitedict import SqliteDict
from bro_sync.api import WssApiCaller
from bro_sync.ctx import Ctx

log = logging.getLogger("bro-sync")


class RemoteTreeDataManager:

    WSS_CLIENT_PAYLOAD_MAX_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, workDir, shareID):
        self.WORK_DIR_ABS_PATH_STR = os.path.abspath(workDir)
        self.SHARE_ID = shareID

        self._bloonRootDir = None
        self._broSyncDbFileAbsPath = None
        self._treeData_remote_current = None
        self._treeData_remote_previous = None
        self._folders_and_files_diff_list_for_action = None

        self._apiUrl = Ctx.BLOON_ADJ_API_WSS_URL

        self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if Ctx.CLOSE_SSL_CERT_VERIFY:
            self._ssl_context.check_hostname = False  # for test only
            self._ssl_context.verify_mode = ssl.CERT_NONE  # for test only

    """
    ==================================================
    Simple getter/setter def. START
    ==================================================
    """

    def getWorkDir(self):
        return self.WORK_DIR_ABS_PATH_STR

    def getBloonRootDir(self):
        return self._bloonRootDir

    def getCurrentTreeDataRemote(self):
        return self._treeData_remote_current

    def getPreviousTreeDataRemote(self):
        """
        Return None if no data stored or any kind of err. 
        """
        return self._treeData_remote_previous

    def getDiffForAction(self):
        """
        return a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        """
        return self._folders_and_files_diff_list_for_action

    """
    ==================================================
    Simple getter/setter def. END
    ==================================================
    """

    def storeCurrentAsPrevious(self):
        if self._bloonRootDir is None:
            log.debug("[INFO] Please call retrieveCurrentRemoteTreeData_async() first.")
        else:
            with SqliteDict(self._broSyncDbFileAbsPath, tablename="ctx") as ctx_db:
                ctx_db.clear()
                ctx = self._treeData_remote_current["ctx"]
                for tmpKey in ctx:
                    tmpVal = ctx[tmpKey]
                    ctx_db[tmpKey] = tmpVal
                ctx_db.commit()

            with SqliteDict(self._broSyncDbFileAbsPath, tablename="folder_set") as folder_set_db:
                folder_set_db.clear()
                folder_set = self._treeData_remote_current["folder_set"]
                for tmpKey in folder_set:
                    folder_set_db[tmpKey] = None
                folder_set_db.commit()

            with SqliteDict(self._broSyncDbFileAbsPath, tablename="file_dict") as file_dict_db:
                file_dict_db.clear()
                file_dict = self._treeData_remote_current["file_dict"]
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
        folder_set__current = self._treeData_remote_current["folder_set"]
        folder_set__previous = {} if self._treeData_remote_previous is None else self._treeData_remote_previous["folder_set"]

        # all new file path need to download
        deff_folder_set = folder_set__current.keys() - folder_set__previous.keys()
        folder_paths_need_to_make.extend(deff_folder_set)

        # --------------------------------------------------
        # for files
        # --------------------------------------------------
        file_dict__current = self._treeData_remote_current["file_dict"]
        file_dict__previous = {} if self._treeData_remote_previous is None else self._treeData_remote_previous["file_dict"]

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

        # log.debug("folder_paths_need_to_make: " + str(folder_paths_need_to_make))
        # log.debug("file_paths_need_to_download: " + str(file_paths_need_to_download))

        self._folders_and_files_diff_list_for_action = (folder_paths_need_to_make, file_paths_need_to_download)

    def loadPreviousTreeDataRemote(self):
        if self._bloonRootDir is None:
            log.debug("[INFO] Please call retrieveCurrentRemoteTreeData_async() first.")
        else:
            if not os.path.exists(self._broSyncDbFileAbsPath):
                return None

            treeData = {}

            with SqliteDict(self._broSyncDbFileAbsPath, tablename="ctx") as ctx_db:
                ctx_mem = {}
                for tmpKey in ctx_db:
                    tmpVal = ctx_db[tmpKey]
                    ctx_mem[tmpKey] = tmpVal
                treeData["ctx"] = ctx_mem

            with SqliteDict(self._broSyncDbFileAbsPath, tablename="folder_set") as folder_set_db:
                folder_set_mem = {}
                for tmpKey in folder_set_db:
                    folder_set_mem[tmpKey] = None
                treeData["folder_set"] = folder_set_mem

            with SqliteDict(self._broSyncDbFileAbsPath, tablename="file_dict") as file_dict_db:
                file_dict_mem = {}
                for tmpKey in file_dict_db:
                    tmpVal = file_dict_db[tmpKey]
                    file_dict_mem[tmpKey] = tmpVal
                treeData["file_dict"] = file_dict_mem

            self._treeData_remote_previous = treeData

    async def retrieveCurrentRemoteTreeData_async(self):

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

        async with websockets.connect(self._apiUrl, ssl=self._ssl_context, max_size=RemoteTreeDataManager.WSS_CLIENT_PAYLOAD_MAX_SIZE) as wss:
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

                    self._bloonRootDir = os.path.join(self.WORK_DIR_ABS_PATH_STR, root_localRelPath)
                    log.debug("[DEBUG] __bloonRootDir: [" + self._bloonRootDir + "]")

                    self._broSyncDbFileAbsPath = os.path.join(self.WORK_DIR_ABS_PATH_STR, Ctx.DB_FILE_NAME)
                    log.debug("[DEBUG] __broSyncDbFileAbsPath: [" + self._broSyncDbFileAbsPath + "]")

                    self._handle_childFiles(root_localRelPath, childCards, treeData)

                    for childFolder in childFolders:
                        chF_isRecycled = childFolder["isRecycled"]
                        if not chF_isRecycled:
                            chF_name = childFolder["name"]
                            chF_folderID = childFolder["folderID"]
                            chF_localRelPath = root_localRelPath + "/" + chF_name
                            await self._getChildFolderRecursiveUnit_async(api, self.SHARE_ID, chF_folderID, chF_localRelPath, treeData)

            else:
                """
                It will enter this block only if item itself of this sharelink is not a folder.
                """
                # outAll = await api.getCard_async({"shareID": shareID, "cardID": itemID})
                # outData = outAll["data"]
                # log.debug(outData)
                log.debug("[INFO] This sharelink is not a folder.")

        self._treeData_remote_current = treeData

    @staticmethod
    async def _getChildFolderRecursiveUnit_async(api, shareID, folderID, localRelPath, treeData):

        treeData["folder_set"][localRelPath] = None

        outAll = await api.getFolder_async({"shareID": shareID, "folderID": folderID})
        outData = outAll["data"]
        isRecycled = outData["isRecycled"]
        if not isRecycled:
            # name = outData["name"] # no use for now
            childCards = outData["childCards"]
            childFolders = outData["childFolders"]

        RemoteTreeDataManager._handle_childFiles(localRelPath, childCards, treeData)

        for childFolder in childFolders:
            chF_isRecycled = childFolder["isRecycled"]
            if not chF_isRecycled:
                chF_name = childFolder["name"]
                chF_folderID = childFolder["folderID"]
                chF_localRelPath = localRelPath + "/" + chF_name
                await RemoteTreeDataManager._getChildFolderRecursiveUnit_async(api, shareID, chF_folderID, chF_localRelPath, treeData)

    @staticmethod
    def _handle_childFiles(localRelPath, childCards, treeData):

        for childCard in childCards:
            chC_isRecycled = childCard["isRecycled"]
            if not chC_isRecycled:
                chC_name = childCard["name"]
                chC_extension = childCard["extension"]
                chC_version = childCard["version"]  # int
                chC_checksum_b64str = childCard["checksum"]  # binary in base64 format string
                chC_checksum_str = base64.b64decode(chC_checksum_b64str).decode("UTF-8")

                if chC_extension:
                    chC_localRelPath = localRelPath + "/" + chC_name + "." + chC_extension
                else:
                    chC_localRelPath = localRelPath + "/" + chC_name

                treeData["file_dict"][chC_localRelPath] = (chC_version, chC_checksum_str)
