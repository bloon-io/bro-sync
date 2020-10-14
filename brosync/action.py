import asyncio
import os
import urllib.request
import ssl
import json
import shutil
from brosync.tree_data import RemoteTreeDataManager
from brosync.ctx import Ctx


class DiffActionAgent:

    def __init__(self):
        pass

    def doDiffAction(self, rtdm):
        """
        rtdm is RemoteTreeDataManager obj.
        """
        # to creat all folders in diff. list
        DiffActionAgent._createFoldersByDiff(rtdm)

        # to download all files in diff. list
        DiffActionAgent._createFilesByDiff(rtdm)

        # to compare local tree and del garbage files & folders
        DiffActionAgent._deleteItemsByLocalDiffWithRemote(rtdm)

    @staticmethod
    def _create_checksumRevIdxDict(treeData):
        if not treeData:
            return {}

        crid = {}  # crid: Checksum Reversed Idx Dict
        file_dict = treeData["file_dict"]

        for rel_path in file_dict.keys():
            checksum_str = file_dict[rel_path][1]
            crid[checksum_str] = rel_path
        return crid

    @staticmethod
    def _deleteItemsByLocalDiffWithRemote(rtdm):

        item_tuple = DiffActionAgent._createLocalItemSet(rtdm)
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

        print("----------")
        print("folder_paths_need_to_del")
        print("----------")
        print(json.dumps(folder_paths_need_to_del, indent=4, ensure_ascii=False))  # for debug only

        print()
        print("----------")
        print("file_paths_need_to_del")
        print("----------")
        print(json.dumps(file_paths_need_to_del, indent=4, ensure_ascii=False))  # for debug only
        print()

        for to_del_rel_path in folder_paths_need_to_del:
            to_del_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, to_del_rel_path)
            try:
                shutil.rmtree(to_del_abs_path)
                print("[DEBUG] rmtree: [" + to_del_abs_path + "]")
            except:
                pass

        for to_del_rel_path in file_paths_need_to_del:
            to_del_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, to_del_rel_path)
            try:
                os.remove(to_del_abs_path)
                print("[DEBUG] rm file: [" + to_del_abs_path + "]")
            except:
                pass

    @staticmethod
    def _createLocalItemSet(rtdm):
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
    def _createFilesByDiff(rtdm):
        current_file_dict = rtdm.getCurrentTreeDataRemote()["file_dict"]
        crid_previous = DiffActionAgent._create_checksumRevIdxDict(rtdm.getPreviousTreeDataRemote())  # crid: Checksum Reversed Idx Dict

        # diffListForAction is a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        diffListForAction = rtdm.getDiffForAction()
        file_paths_need_to_download = diffListForAction[1]
        for fileRelPath in file_paths_need_to_download:
            checksum = current_file_dict[fileRelPath][1]

            same_file_rel_path_previous = crid_previous.get(checksum)
            if same_file_rel_path_previous:
                try:
                    DiffActionAgent._createFileByCopy(rtdm, fileRelPath, same_file_rel_path_previous)
                except Exception as e:
                    print("[WARN] copy file exception. e: [" + str(e) + "]")
                    DiffActionAgent._createFileByDownload(rtdm, fileRelPath)
            else:
                DiffActionAgent._createFileByDownload(rtdm, fileRelPath)

    @staticmethod
    def _createFileByDownload(rtdm, fileRelPath):
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
    def _createFoldersByDiff(rtdm):
        # diffListForAction is a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        diffListForAction = rtdm.getDiffForAction()
        folder_paths_need_to_make = diffListForAction[0]
        for folderRelPath in folder_paths_need_to_make:
            absPath = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, folderRelPath)
            print("[DEBUG] mkdir -p: [" + absPath + "]")
            os.makedirs(absPath, exist_ok=True)

    @staticmethod
    def _createFileByCopy(rtdm, fileRelPath, same_file_rel_path_previous):
        src_file_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, same_file_rel_path_previous)
        dest_file_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, fileRelPath)
        shutil.copy2(src_file_abs_path, dest_file_abs_path)
        print("[DEBUG] copy file, from [" + same_file_rel_path_previous + "], to [" + fileRelPath + "]")

    # @staticmethod
    # def _createFileByMove(rtdm, fileRelPath, same_file_rel_path_previous):
    #     src_file_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, same_file_rel_path_previous)
    #     dest_file_abs_path = os.path.join(rtdm.WORK_DIR_ABS_PATH_STR, fileRelPath)
    #     shutil.move(src_file_abs_path, dest_file_abs_path)
    #     print("[DEBUG] move file, from [" + same_file_rel_path_previous + "], to [" + fileRelPath + "]")