import asyncio
import os
from TreeDataManager import TreeDataManager

class DiffActionAgent:

    def __init__(self):
        pass
        
    def doDiffAction(self, tdm):
        """
        tdm is TreeDataManager obj.
        """
        # diffListForAction is a tuple: (folder_paths_need_to_make, file_paths_need_to_download)
        diffListForAction = tdm.getDiffForAction()
        folder_paths_need_to_make = diffListForAction[0]
        file_paths_need_to_download = diffListForAction[1]

        for folderRelPath in folder_paths_need_to_make:
            absPath = os.path.join(tdm.WORK_DIR_ABS_PATH_STR, folderRelPath)
            print("[DEBUG] mkdir -p: [" + absPath + "]")
            os.makedirs(absPath, exist_ok=True)

        for fileRelPath in file_paths_need_to_download:
            download_link = fileRelPath
            print("[DEBUG] download_link: [" + download_link + "]")



        
        # TODO to creat folder all list
        # TODO to download all files (optimize by checksumRevIdx table)
        # TODO to compare local tree
        # TODO to del garbage files & folders

        pass

        

