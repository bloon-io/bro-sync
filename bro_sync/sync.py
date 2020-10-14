
import asyncio
import json
import time
from bro_sync.tree_data import RemoteTreeDataManager
from bro_sync.action import DiffActionAgent
from bro_sync.ctx import Ctx


class BroSync:

    def __init__(self, shareID, workDir):
        self.shareID = shareID
        self.workDir = workDir

    async def start_sync_service_async(self):
        print("[INFO] bro-sync servcie start.")
        try:
            while True:
                await self.sync_once_async()
                time.sleep(Ctx.SERVICE_SYNC_LOOP_INTERVAL)
        except:
            print("[INFO] bro-sync servcie stop.")

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
