import asyncio
import json
import sys
import textwrap
from bro_sync.tree_data import RemoteTreeDataManager
from bro_sync.action import DiffActionAgent
from bro_sync.sync import BroSync


class Main:

    SHARE_ID = None
    WORK_DIR = None

    async def main(self):
        shareId = sys.argv[1] if len(sys.argv) >= 2 else Main.SHARE_ID
        workDir = sys.argv[2] if len(sys.argv) >= 3 else Main.WORK_DIR

        if (not shareId) or (not workDir):
            print(textwrap.dedent("""
                Usage: python main.py SHARE_ID WORK_DIR
                SHARE_ID is a BLOON sharelink ID of your folder.
                WORK_DIR is the place you want to put your sync. folder.

                The following line shows how to get an ID from a sharelink:
                https://www.bloon.io/share/[a sharelink ID]/

                How to get a shearlink? See https://www.bloon.io/help/sharelinks
                """))
            return

        # --------------------------------------------------
        broSync = BroSync(shareId, workDir)
        await broSync.sync_once_async()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
