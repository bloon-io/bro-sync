import asyncio
import os
import urllib.request
import ssl
from RemoteTreeDataManager import RemoteTreeDataManager
from Ctx import Ctx


class DiffActionAgent:

    def __init__(self):
        pass

    def doDiffAction(self, tdm):
        """
        tdm is RemoteTreeDataManager obj.
        """
        # to creat all folders in diff. list
        DiffActionAgent.__createFoldersByDiff(tdm)

        # to download all files in diff. list
        DiffActionAgent.__downloadFilesByDiff(tdm)

        # TODO to compare local tree and del garbage files & folders
        
        # TODO now-here to create local folders set & files set

        # TODO to optimize download by checksumRevIdx table (move rather than download)

    @staticmethod
    def __downloadFilesByDiff(tdm):
        # diffListForAction is a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        diffListForAction = tdm.getDiffForAction()
        file_paths_need_to_download = diffListForAction[1]
        for fileRelPath in file_paths_need_to_download:
            direct_link = Ctx.BLOON_DIRECT_LINK_URL_BASE + "/" + tdm.SHARE_ID
            bloon_name = tdm.getCurrentTreeDataRemote()["ctx"]["bloon_name"]
            directLinkRelPath = fileRelPath[len(bloon_name) + 1:]  # remove leading bloon name, "+1" is for char "/"
            directLinkRelPath = urllib.parse.quote(directLinkRelPath)  # url percent-encoding

            download_link = direct_link + "/" + directLinkRelPath
            print("[DEBUG] download_link: [" + download_link + "]")

            file_abs_path = os.path.join(tdm.WORK_DIR_ABS_PATH_STR, fileRelPath)
            # print("[DEBUG] download file_abs_path: [" + file_abs_path + "]")

            if Ctx.CLOSE_SSL_CERT_VERIFY:
                ssl._create_default_https_context = ssl._create_unverified_context

            urllib.request.urlretrieve(download_link, file_abs_path)

    @staticmethod
    def __createFoldersByDiff(tdm):
        # diffListForAction is a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        diffListForAction = tdm.getDiffForAction()
        folder_paths_need_to_make = diffListForAction[0]
        for folderRelPath in folder_paths_need_to_make:
            absPath = os.path.join(tdm.WORK_DIR_ABS_PATH_STR, folderRelPath)
            print("[DEBUG] mkdir -p: [" + absPath + "]")
            os.makedirs(absPath, exist_ok=True)
