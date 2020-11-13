
import asyncio
import pathlib
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
from bro_sync.utils import Utils

log = logging.getLogger("bro-sync")


class RemoteTreeDataManager:

    WSS_CLIENT_PAYLOAD_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    REMOTE_VERSION = 0
    IGNORE_CARD_TYPE = [3, 5, 11, 12, 13, 14]

    def __init__(self, workDir, shareID):
        self.WORK_DIR_ABS_PATH_STR = os.path.abspath(workDir)
        self.SHARE_ID = shareID

        self._bloonRootDir = None
        self._broSyncDbFileAbsPath = None
        self._treeData_remote_current = None
        self._treeData_remote_previous = None
        self._folders_and_files_diff_list_for_action = None

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
            log.debug("call retrieveCurrentRemoteTreeData_async() first.")
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
                    tmpVal = folder_set[tmpKey]
                    folder_set_db[tmpKey] = tmpVal
                folder_set_db.commit()

            with SqliteDict(self._broSyncDbFileAbsPath, tablename="file_dict") as file_dict_db:
                file_dict_db.clear()
                file_dict = self._treeData_remote_current["file_dict"]
                for tmpKey in file_dict:
                    tmpVal = file_dict[tmpKey]
                    file_dict_db[tmpKey] = tmpVal
                file_dict_db.commit()

    def updateDiffListForAction(self):
        folder_paths_need_to_make = []
        file_paths_need_to_download = []

        # --------------------------------------------------
        # for folders
        # --------------------------------------------------
        folder_set__current = self._treeData_remote_current["folder_set"]
        folder_set__previous = {} if self._treeData_remote_previous is None else self._treeData_remote_previous["folder_set"]

        # all new file path need to download
        diff_folder_set = folder_set__current.keys() - folder_set__previous.keys()
        folder_paths_need_to_make.extend(diff_folder_set)

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
            log.debug("call retrieveCurrentRemoteTreeData_async() first.")
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
                    tmpVal = folder_set_db[tmpKey]
                    folder_set_mem[tmpKey] = tmpVal
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

        
        async with websockets.connect(Ctx.BLOON_ADJ_API_WSS_URL, ssl=Ctx.API_WSS_SSL_CONTEXT, max_size=RemoteTreeDataManager.WSS_CLIENT_PAYLOAD_MAX_SIZE) as wss:
            api = WssApiCaller(wss)
            outData = await api.getShareInfo_async({"shareID": self.SHARE_ID})
            version = outData["version"]
            log.debug("share link version " + str(version))
            waitTs = 0
            while RemoteTreeDataManager.REMOTE_VERSION != 0 and RemoteTreeDataManager.REMOTE_VERSION > version:
                waitTs += 1
                log.info("server version is old, wait " + str(waitTs) + " sec...")
                await asyncio.sleep(waitTs)
                outData = await api.getShareInfo_async({"shareID": self.SHARE_ID})
                version = outData["version"]

            shareData = outData["shareData"]
            itemID = shareData["itemID"]
            isFolder = shareData["isFolder"]
            bloonID = shareData["bloonID"]

            if isFolder:
                await self._getChildFolderRecursiveUnit_async(api, self.SHARE_ID, bloonID, [itemID], "", treeData)

            else:
                """
                It will enter this block only if item itself of this sharelink is not a folder.
                """
                # outAll = await api.getCard_async({"shareID": shareID, "cardID": itemID})
                # outData = outAll["data"]
                # log.debug(outData)
                log.info("This sharelink is not a folder.")


        self._treeData_remote_current = treeData

    async def _getChildFolderRecursiveUnit_async(self, api, shareID, bloonID, folderIDs, localRelPath, treeData):

        retData = await api.getFoldersMin_async({"shareID": shareID, "bloonID": bloonID, "folderIDs": folderIDs})
        folderDatas = retData["folders"]
        for folder in folderDatas:
            folderID = folder["folderID"]
            name = folder["name"]
            folderName = Utils.getAvailableFileBaseName(name, True)
            childCards = []
            childRelPath = ""

            if not localRelPath:
                # mean it is root
                treeData["ctx"]["bloon_name"] = name
                root_localRelPath = folderName

                self._bloonRootDir = os.path.join(self.WORK_DIR_ABS_PATH_STR, root_localRelPath)
                log.debug("_bloonRootDir: [" + self._bloonRootDir + "]")

                self._broSyncDbFileAbsPath = os.path.join(self.WORK_DIR_ABS_PATH_STR, Ctx.DB_FILE_NAME)
                log.debug("_broSyncDbFileAbsPath: [" + self._broSyncDbFileAbsPath + "]")

                childRelPath = root_localRelPath
            else:
                childRelPath = localRelPath + "/" + folderName
                index = 0
                while childRelPath in treeData["folder_set"]:
                    log.debug("folder path exist : " + str(childRelPath))
                    index += 1
                    childRelPath = localRelPath + "/" + Utils.getFileName(folderName, '', index)

                
            treeData["folder_set"][childRelPath] = folderID

            if len(folder["childCardIDs"]) > 0:
                retData = await api.getCardsMin_async({"shareID": shareID, "bloonID": bloonID, "cardIDs": folder["childCardIDs"]})
                childCards = retData["cards"]
                    
            self._handle_childFiles(childRelPath, childCards, treeData)

            if len(folder["childFolderIDs"]) > 0:
                await self._getChildFolderRecursiveUnit_async(api, shareID, bloonID, folder["childFolderIDs"], childRelPath, treeData)

    @staticmethod
    def _handle_childFiles(localRelPath, childCards, treeData):

        for childCard in childCards:
            if childCard["typeInt"] in RemoteTreeDataManager.IGNORE_CARD_TYPE:
                log.debug("Ignore Non-File Card...")
                continue
            chC_id = childCard["cardID"]
            chC_extension = childCard["extension"]
            chC_name = Utils.getAvailableFileBaseName(childCard["name"], not chC_extension)
            chC_version = childCard["version"]  # int
            chC_checksum_b64str = childCard["checksum"]  # binary in base64 format string
            chC_checksum_str = base64.b64decode(chC_checksum_b64str).decode("UTF-8")

            index = 0
            chC_localRelPath = localRelPath + "/" + Utils.getFileName(chC_name, chC_extension, index)
            while chC_localRelPath in treeData["file_dict"]:
                log.debug("file path exist : " + str(chC_localRelPath))
                index += 1
                chC_localRelPath = localRelPath + "/" + Utils.getFileName(chC_name, chC_extension, index)

            treeData["file_dict"][chC_localRelPath] = (chC_version, chC_checksum_str, chC_id)
