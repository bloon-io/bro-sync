
import asyncio
import json
import time
import logging
from bro_sync.tree_data import RemoteTreeDataManager
from bro_sync.action import DiffActionAgent
from bro_sync.ctx import Ctx

log = logging.getLogger("bro-sync")


class BroSync:

    def __init__(self, shareID, workDir):
        self.shareID = shareID
        self.workDir = workDir

    async def start_sync_service_async(self):
        log.debug("[INFO] bro-sync servcie start.")
        try:
            while True:
                await self.sync_once_async()
                time.sleep(Ctx.SERVICE_SYNC_LOOP_INTERVAL)
        except:
            log.debug("[INFO] bro-sync servcie stop.")

    async def sync_once_async(self):
        rtdm = RemoteTreeDataManager(self.workDir, self.shareID)

        # --------------------------------------------------
        await rtdm.retrieveCurrentRemoteTreeData_async()
        treeData_remote_current = rtdm.getCurrentTreeDataRemote()
        log.debug("----------")
        log.debug("current")
        log.debug("----------")
        # log.debug(treeData_remote_current)
        log.debug(json.dumps(treeData_remote_current, indent=4, ensure_ascii=False))  # for debug only
        log.debug("")

        # --------------------------------------------------
        rtdm.loadPreviousTreeDataRemote()
        treeData_remote_previous = rtdm.getPreviousTreeDataRemote()
        log.debug("----------")
        log.debug("previous")
        log.debug("----------")
        # log.debug(treeData_remote_previous)
        log.debug(json.dumps(treeData_remote_previous, indent=4, ensure_ascii=False))  # for debug only
        log.debug("")

        # --------------------------------------------------
        rtdm.createDiffListForAction()
        diffListTuple = rtdm.getDiffForAction()
        log.debug("----------")
        log.debug("diff")
        log.debug("----------")
        log.debug(json.dumps(diffListTuple, indent=4, ensure_ascii=False))  # for debug only
        log.debug("")

        # --------------------------------------------------
        daa = DiffActionAgent()
        daa.doDiffAction(rtdm)

        # --------------------------------------------------
        rtdm.storeCurrentAsPrevious()
