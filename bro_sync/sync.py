
import asyncio
import json
from bro_sync.tree_data import RemoteTreeDataManager
from bro_sync.action import DiffActionAgent


class BroSync:

    def __init__(self, shareID, workDir):
        self.shareID = shareID
        self.workDir = workDir

    async def sync_once_async(self):

        rtdm = RemoteTreeDataManager(self.workDir, self.shareID)

        # --------------------------------------------------
        await rtdm.retrieveCurrentRemoteTreeData_async()
        treeData_remote_current = rtdm.getCurrentTreeDataRemote()
        print("----------")
        print("current")
        print("----------")
        # print(treeData_remote_current)
        print(json.dumps(treeData_remote_current, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        rtdm.loadPreviousTreeDataRemote()
        treeData_remote_previous = rtdm.getPreviousTreeDataRemote()
        print("----------")
        print("previous")
        print("----------")
        # print(treeData_remote_previous)
        print(json.dumps(treeData_remote_previous, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        rtdm.createDiffListForAction()
        diffListTuple = rtdm.getDiffForAction()
        print("----------")
        print("diff")
        print("----------")
        print(json.dumps(diffListTuple, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        daa = DiffActionAgent()
        daa.doDiffAction(rtdm)

        # --------------------------------------------------
        rtdm.storeCurrentAsPrevious()

    def start_sync_service(self):
        pass