import asyncio
from Main import Main

class LocalActionManager:

    def __init__(self):
        pass

    def doDiffAction(self):
        # TODO now-here to impl.
        # (folder_paths_need_to_make, file_paths_need_to_download)
        pass


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())