import asyncio
import sys
import textwrap
import argparse
import logging
from argparse import RawTextHelpFormatter
from bro_sync.sync import BroSync

log = logging.getLogger("bro-sync")
log.setLevel(logging.INFO)

log_stdout_handler = logging.StreamHandler(sys.stdout)
log_stdout_handler.setLevel(logging.NOTSET)
formatter = logging.Formatter("%(levelname)s %(message)s")
log_stdout_handler.setFormatter(formatter)

log.addHandler(log_stdout_handler)


class BroSyncRawTextHelpFormatter(RawTextHelpFormatter):
    def __init__(self, *args, max_help_position=36, **kwargs):
        super(BroSyncRawTextHelpFormatter, self).__init__(*args, max_help_position=max_help_position, **kwargs)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to 
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    #parts.append('%s %s' % (option_string, args_string))
                    parts.append('%s' % option_string)
                parts[-1] += ' %s'%args_string
            return ', '.join(parts)

class Main:

    async def main(self):

        parser = argparse.ArgumentParser(description=textwrap.indent(textwrap.dedent("""
                To synchronize the folder you shared through a BLOON sharelink.

                The following line shows how to get an ID from a sharelink:
                https://www.bloon.io/share/[a sharelink ID]/

                How to get a sharelink?
                See https://www.bloon.io/help/sharelinks
                """), "  "), formatter_class=BroSyncRawTextHelpFormatter)

        parser.add_argument("SHARE_ID", type=str, help="A BLOON sharelink ID of your folder.")

        actions = parser.add_mutually_exclusive_group(required=True)
        actions.add_argument("-s", "--sync", metavar='WORK_DIR', help="start and keep syncing")
        actions.add_argument("-t", "--no-stash-transfer", metavar='dir_path', help="wait and receive file directly without staging in bloon")
        
        parser.add_argument("-q", "--quiet", action="store_true", default=False, help="run quietly, show nothing on screen")
        parser.add_argument("--service", action="store_true", default=False, help="start and keep syncing")
        parser.add_argument("--detail", action="store_true", default=False, help="show more details on screen")
        args = parser.parse_args()

        # --------------------------------------------------
        if args.quiet:
            log.setLevel(logging.FATAL)
        elif args.detail:
            log.setLevel(logging.DEBUG)
        
        if args.no_stash_transfer:
            broSync = BroSync(args.SHARE_ID, args.no_stash_transfer)
            await broSync.start_transfer_file_async()
        else:
            broSync = BroSync(args.SHARE_ID, args.sync)
            if args.service:
                await broSync.start_sync_service_async()
            else:
                await broSync.start_sync_once_async()


if __name__ == "__main__":
    try:
        # asyncio.get_event_loop().run_until_complete(Main().main())
        asyncio.run(Main().main())
    except KeyboardInterrupt:
        log.info("exit bro-sync...")
