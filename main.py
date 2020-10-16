import asyncio
import json
import sys
import textwrap
import argparse
import logging
from argparse import RawTextHelpFormatter
from bro_sync.tree_data import RemoteTreeDataManager
from bro_sync.action import DiffActionAgent
from bro_sync.sync import BroSync

logging.basicConfig(format="%(levelname)s %(message)s")
log = logging.getLogger("bro-sync")
log.setLevel(logging.INFO)


class Main:

    async def main(self):

        parser = argparse.ArgumentParser(description=textwrap.indent(textwrap.dedent("""
                To synchronize a folder you shared through a BLOON sharelink.

                The following line shows how to get an ID from a sharelink:
                https://www.bloon.io/share/[a sharelink ID]/

                How to get a shearlink?
                See https://www.bloon.io/help/sharelinks
                """), "  "), formatter_class=RawTextHelpFormatter)

        parser.add_argument("SHARE_ID", type=str, help="A BLOON sharelink ID of your folder.")
        parser.add_argument("WORK_DIR", type=str, help="The place you want to put your sync. folder.")
        parser.add_argument("-s", "--service", action="store_true", default=False, help="start and keep syncing")
        parser.add_argument("-q", "--quiet", action="store_true", default=False, help="run quietly, show nothing on screen")
        parser.add_argument("--detail", action="store_true", default=False, help="show more details on screen")
        args = parser.parse_args()

        # --------------------------------------------------
        broSync = BroSync(args.SHARE_ID, args.WORK_DIR)

        if args.quiet:
            log.setLevel(logging.FATAL)
        elif args.detail:
            log.setLevel(logging.DEBUG)

        if args.service:
            await broSync.start_sync_service_async()
        else:
            await broSync.sync_once_async()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
