import asyncio
import json
from TreeDataManager import TreeDataManager
from DiffActionAgent import DiffActionAgent


class Main:

    async def main(self):
        shareID = "WjCz6B10"  # test data NBNO3
        # shareID = "JJ5RWaBV"  # test data
        # shareID = "WZys1ZoW" # test data
        # workDir = "C:\\Users\\patwnag\\Desktop\\" # TOPNO3
        workDir = "C:\\Users\\patwang\\Desktop\\" # NBNO3, TOPNO2
        tdm = TreeDataManager(workDir, shareID)

        # --------------------------------------------------
        await tdm.retrieveCurrentTreeDataRemote_async()
        treeData_remote_current = tdm.getCurrentTreeDataRemote()
        print("----------")
        print("current")
        print("----------")
        # print(treeData_remote_current)
        print(json.dumps(treeData_remote_current, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        tdm.loadPreviousTreeDataRemote()
        treeData_remote_previous = tdm.getPreviousTreeDataRemote()
        print("----------")
        print("previous")
        print("----------")
        # print(treeData_remote_previous)
        print(json.dumps(treeData_remote_previous, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        tdm.createDiffListForAction()
        diffListTuple = tdm.getDiffForAction()
        print("----------")
        print("diff")
        print("----------")
        print(json.dumps(diffListTuple, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        daa = DiffActionAgent()
        daa.doDiffAction(tdm)

        # --------------------------------------------------
        tdm.storeCurrentAsPrevious()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
