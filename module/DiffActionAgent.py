import asyncio
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
        
        if self.isBloonRootChangeName(tdm):
            pass


        # TODO to check bloon root chage name, to do mv
        # TODO to creat folder all list
        # TODO to download all files (optimize by checksumRevIdx table)
        # TODO to compare local tree
        # TODO to del garbage files & folders

        pass

    def isBloonRootChangeName(self, tdm):
        print(tdm.WORK_DIR_ABS_PATH_STR)
        print(tdm.getBloonRootDir())
        

