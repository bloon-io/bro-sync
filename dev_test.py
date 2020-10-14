
import asyncio
from main import Main

# TODO manage log (make DEBUG closable)
# TODO impl. BroSync.start_sync_service
# TODO test in linux env.
# TODO write README

Main.SHARE_ID = "klUReHe5"  # test data HW TOPNO2
# Main.SHARE_ID = "OXrq5h3g"  # test data HW TOPNO3
# Main.SHARE_ID = "WjCz6B10"  # test data HW NBNO3
Main.WORK_DIR = "C:\\Users\\patwnag\\Desktop\\"  # HW TOPNO2
# Main.WORK_DIR = "C:\\Users\\patwang\\Desktop\\"  # HW NBNO3, HW TOPNO3


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
