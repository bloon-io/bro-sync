
import asyncio
import json
import logging
import websockets
import threading
from datetime import datetime
from bro_sync.tree_data import RemoteTreeDataManager
from bro_sync.action import DiffActionAgent
from bro_sync.ctx import Ctx
from bro_sync.api import WssApiListener


log = logging.getLogger("bro-sync")


class BroSync:

    def __init__(self, shareID, workDir):
        self.shareID = shareID
        self.workDir = workDir
        self._lastSyncTime = 0.0
        self._hasSync = False

    async def start_sync_service_async(self):
        log.info("bro-sync servcie start.")
        while True:
            try:
                if not self._hasSync:
                    await self.sync_once_async()
                    self._hasSync = True
                async with websockets.connect(Ctx.BLOON_ADJ_API_WSS_URL, ssl=Ctx.API_WSS_SSL_CONTEXT) as wss:
                    listener = WssApiListener(wss)
                    if not await listener.startListen(self.shareID):
                        log.info("re-try after 5s...")
                        await asyncio.sleep(5)
                        continue
                    log.info("start listen event...")
                    while True:
                        eventData = await listener.recvEventMessage()
                        if eventData:
                            self._lastSyncTime = datetime.now().timestamp()
                            log.info("listen event " + str(eventData))
                            # run at anther thread
                            th = threading.Thread(target=self.delay_sync_server_in_event_loop, args=(self._lastSyncTime,))
                            th.start()

            except BaseException as e:
                log.info("exception reason: [" + str(e) + "]")
                log.info("re-try after 5s...")
                await asyncio.sleep(5)

    def delay_sync_server_in_event_loop(self, syncTime):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.delay_sync_server_async(syncTime))
        loop.close()

    async def delay_sync_server_async(self, syncTime):
        await asyncio.sleep(Ctx.SERVICE_SYNC_LOOP_INTERVAL)
        if self._lastSyncTime == syncTime:
            try:
                time_str = datetime.now().strftime("%Y-%m%d %H:%M:%S")
                log.info("----- service action @" + time_str + " -----")
                await self.sync_once_async()
            except BaseException as e:
                log.info("bro-sync sync failed.")
                log.info("reason: [" + str(e) + "]")

    async def sync_once_async(self):
        rtdm = RemoteTreeDataManager(self.workDir, self.shareID)

        # --------------------------------------------------
        await rtdm.retrieveCurrentRemoteTreeData_async()
        treeData_remote_current = rtdm.getCurrentTreeDataRemote()
        log.debug("----------")
        log.debug("treeData_remote_current")
        log.debug("----------")
        log.debug(json.dumps(treeData_remote_current, indent=4, ensure_ascii=False))
        log.debug("")

        # --------------------------------------------------
        rtdm.loadPreviousTreeDataRemote()
        treeData_remote_previous = rtdm.getPreviousTreeDataRemote()
        log.debug("----------")
        log.debug("treeData_remote_previous")
        log.debug("----------")
        log.debug(json.dumps(treeData_remote_previous, indent=4, ensure_ascii=False))
        log.debug("")

        # --------------------------------------------------
        rtdm.updateDiffListForAction()
        diffListTuple = rtdm.getDiffForAction()
        log.debug("----------")
        log.debug("folder_paths_need_to_make & file_paths_need_to_download")
        log.debug("----------")
        log.debug(json.dumps(diffListTuple, indent=4, ensure_ascii=False))
        log.debug("")

        # --------------------------------------------------
        daa = DiffActionAgent()
        daa.doDiffAction(rtdm)

        # --------------------------------------------------
        rtdm.storeCurrentAsPrevious()
