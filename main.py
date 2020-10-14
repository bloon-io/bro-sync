import asyncio
import json
from brosync.tree_data import RemoteTreeDataManager
from brosync.action import DiffActionAgent
from brosync.sync import BroSync



class Main:

    # TODO manage log (make DEBUG closable)

    # TODO impl. BroSync.start_sync_service

    # TODO test in linux env.

    # TODO write README

    async def main(self):
        shareID = "klUReHe5"  # test data HW TOPNO2
        # shareID = "OXrq5h3g"  # test data HW TOPNO3
        # shareID = "WjCz6B10"  # test data HW NBNO3
        workDir = "C:\\Users\\patwnag\\Desktop\\" # HW TOPNO2
        # workDir = "C:\\Users\\patwang\\Desktop\\"  # HW NBNO3, HW TOPNO3

        broSync = BroSync(shareID, workDir)
        await broSync.sync_once_async()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
