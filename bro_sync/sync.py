
import asyncio
import json
import logging
import websockets
import threading
import traceback
import time
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
        self._mutex = threading.Lock()
        self._delay_mode = False
        self._in_sequence_recv_state = False
        self._err_retry_interval = Ctx.SYNC_ERR_RE_TRY_BASE_INTERVAL_SEC

    async def start_sync_once_async(self):
        try:
            await self.sync_once_async()
        except BaseException as e:
            errStr = str(e)
            if errStr == "RESOURCE_NOT_EXIST":
                log.error("the share id is invalid, please check !\n")
                return
            else:
                log.error("exception reason: [" + errStr + "]")
                # traceback.print_exc()

    async def start_sync_service_async(self):
        log.info("bro-sync servcie start...")
        while True:
            try:
                await self.sync_once_async()
                break
            except BaseException as e:
                errStr = str(e)
                if errStr == "RESOURCE_NOT_EXIST":
                    log.error("the share id is invalid, please check !\n")
                    return
                else:
                    log.info("exception reason: [" + errStr + "]")
                    log.info("re-try after 3s...")
                    await asyncio.sleep(3)

        while True:
            try:
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
                            log.debug("listen event " + str(eventData))
                            self._lastSyncTime = datetime.now().timestamp()
                            # run at anther thread
                            threading.Thread(target=self._delay_sync_in_thread, args=(self._lastSyncTime, False), daemon=True).start()

            except BaseException as e:
                log.warning("exception reason: [" + str(e) + "]")
                log.info("re-try after 5s...")
                await asyncio.sleep(5)

    def _delay_sync_in_thread(self, syncTime, is_from_re_try):
        if is_from_re_try:
            log.info("re-try after " + str(self._err_retry_interval) + "s...")
            time.sleep(self._err_retry_interval)
            self._err_retry_interval += 0 if self._err_retry_interval > Ctx.SYNC_ERR_RE_TRY_BASE_INTERVAL_MAX_SEC else Ctx.SYNC_ERR_RE_TRY_BASE_INTERVAL_SEC

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._delay_sync_async(syncTime))
        loop.close()

    async def _delay_sync_async(self, syncTime):
        if self._delay_mode:
            await asyncio.sleep(Ctx.SYNC_DELAY_MODE_DELAY_SEC)
        else:
            self._delay_mode = True
            log.debug("sync delay mode [ON]")
            threading.Thread(target=self._close_delay_mode_after_a_while, daemon=True).start()

        if self._lastSyncTime != syncTime:
            self._in_sequence_recv_state = True
        else:
            self._in_sequence_recv_state = False
            self._mutex.acquire()

            try:
                time_str = datetime.now().strftime("%Y-%m%d %H:%M:%S")
                log.info("----- service action @" + time_str + " -----")
                await self.sync_once_async()
                self._err_retry_interval = Ctx.SYNC_ERR_RE_TRY_BASE_INTERVAL_SEC
            except BaseException as e:
                log.warning("bro-sync sync failed. reason: [" + str(e) + "]")
                # re-try in new thread
                threading.Thread(target=self._delay_sync_in_thread, args=(syncTime, True), daemon=True).start()

            self._mutex.release()

    def _close_delay_mode_after_a_while(self):
        time_to_wait = Ctx.SYNC_DELAY_MODE_DELAY_SEC * (1.1)
        time.sleep(time_to_wait)
        while self._in_sequence_recv_state:
            time.sleep(time_to_wait)
        self._delay_mode = False
        log.debug("sync delay mode [OFF]")

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
