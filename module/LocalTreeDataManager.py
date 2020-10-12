
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


class LocalTreeDataManager:

    DB_FILE_NAME = ".bro-sync.db"

    def __init__(self, workDir):
        self.WORK_DIR_ABS_PATH_STR = os.path.abspath(workDir)

        self.__bloonRootDir = None
        self.__broSyncDbFileAbsPath = None
        self.__treeData_remote_current = None
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

    """
    ==================================================
    Simple getter/setter def. END
    ==================================================
    """

    async def retrieveCurrentTreeDataLocal(self):
        pass

    @staticmethod
    async def __getChildFolderRecursiveUnit(api, shareID, folderID, localRelPath, treeData):
        pass

    @staticmethod
    def __handle_childFiles(localRelPath, childCards, treeData):
        pass