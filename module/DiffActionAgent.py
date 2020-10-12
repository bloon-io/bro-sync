import asyncio
import os
import urllib.request
import ssl
from RemoteTreeDataManager import RemoteTreeDataManager
from Ctx import Ctx
import json
import shutil


class DiffActionAgent:

    def __init__(self):
        pass

    def doDiffAction(self, rtdm):
        """
        rtdm is RemoteTreeDataManager obj.
        """
        # to creat all folders in diff. list
        DiffActionAgent.__createFoldersByDiff(rtdm)

        # to download all files in diff. list
        DiffActionAgent.__downloadFilesByDiff(rtdm)

        # to compare local tree and del garbage files & folders
        DiffActionAgent.__deleteItemsByLocalDiffWithRemote(rtdm)

        # TODO now-here to optimize download by checksumRevIdx table (move rather than download)

        # TODO adding non-file item, e.g. B-doc

    @staticmethod
    def __deleteItemsByLocalDiffWithRemote(rtdm):

        item_tuple = DiffActionAgent.__createLocalItemSet(rtdm)
        local_folder_set = item_tuple[0]
        local_file_set = item_tuple[1]

        # print(json.dumps(local_folder_set, indent=4, ensure_ascii=False))  # for debug only
        # print(json.dumps(local_file_set, indent=4, ensure_ascii=False))  # for debug only

        rtd_current = rtdm.getCurrentTreeDataRemote()
        remote_folder_set = rtd_current["folder_set"]
        remote_file_dict = rtd_current["file_dict"]

        folder_paths_need_to_del = []
        deff_folder_set = local_folder_set.keys() - remote_folder_set.keys()
        folder_paths_need_to_del.extend(deff_folder_set)

        file_paths_need_to_del = []
        deff_file_set = local_file_set.keys() - remote_file_dict.keys()
        file_paths_need_to_del.extend(deff_file_set)

        print(json.dumps(folder_paths_need_to_del, indent=4, ensure_ascii=False))  # for debug only
        print(json.dumps(file_paths_need_to_del, indent=4, ensure_ascii=False))  # for debug only

        for to_del_rel_path in folder_paths_need_to_del:
            to_del_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, to_del_rel_path)
            to_del_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, to_del_rel_path)
            to_del_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, to_del_rel_path)
            
            shutil.rmtree(to_del_abs_path)
            print("[DEBUG] rmtree: [" + to_del_abs_path + "]")

        for to_del_rel_path in file_paths_need_to_del:
            to_del_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, to_del_rel_path)
            try:
                os.remove(to_del_abs_path)
                print("[DEBUG] rm file: [" + to_del_abs_path + "]")
            except:
                pass
            
    @staticmethod
    def __createLocalItemSet(rtdm):
        """
        return a tuple: (folder_set, file_set)
        """
        folder_set = {}
        file_set = {}

        bloonRootDirStr = rtdm.getBloonRootDir()
        work_path_len = len(rtdm.WORK_DIR_ABS_PATH_STR) + 1  # +1 is for "/" in the end
        walkData = os.walk(bloonRootDirStr)
        for relRoot, dirs, files in walkData:

            for name in dirs:
                tmpAbsPath = os.path.join(relRoot, name)
                tmpRelPath = tmpAbsPath[work_path_len:].replace("\\", "/")
                folder_set[tmpRelPath] = None

            for name in files:
                tmpAbsPath = os.path.join(relRoot, name)
                tmpRelPath = tmpAbsPath[work_path_len:].replace("\\", "/")
                file_set[tmpRelPath] = None

        # adding bloon root dir itself
        folder_set[bloonRootDirStr[work_path_len:]] = None

        return (folder_set, file_set)

    @staticmethod
    def __downloadFilesByDiff(rtdm):
        # diffListForAction is a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        diffListForAction = rtdm.getDiffForAction()
        file_paths_need_to_download = diffListForAction[1]
        for fileRelPath in file_paths_need_to_download:
            direct_link = Ctx.BLOON_DIRECT_LINK_URL_BASE + "/" + rtdm.SHARE_ID
            bloon_name = rtdm.getCurrentTreeDataRemote()["ctx"]["bloon_name"]
            directLinkRelPath = fileRelPath[len(bloon_name) + 1:]  # remove leading bloon name, "+1" is for char "/"
            directLinkRelPath = urllib.parse.quote(directLinkRelPath)  # url percent-encoding

            download_link = direct_link + "/" + directLinkRelPath
            print("[DEBUG] download_link: [" + download_link + "]")

            file_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, fileRelPath)
            # print("[DEBUG] download file_abs_path: [" + file_abs_path + "]")

            if Ctx.CLOSE_SSL_CERT_VERIFY:
                ssl._create_default_https_context = ssl._create_unverified_context

            urllib.request.urlretrieve(download_link, file_abs_path)

    @staticmethod
    def __createFoldersByDiff(rtdm):
        # diffListForAction is a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        diffListForAction = rtdm.getDiffForAction()
        folder_paths_need_to_make = diffListForAction[0]
        for folderRelPath in folder_paths_need_to_make:
            absPath = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, folderRelPath)
            print("[DEBUG] mkdir -p: [" + absPath + "]")
            os.makedirs(absPath, exist_ok=True)
