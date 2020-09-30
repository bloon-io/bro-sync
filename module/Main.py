import asyncio
from TreeDataManager import TreeDataManager
from DiffActionAgent import DiffActionAgent

class Main:

    async def main(self):
        shareID = "JJ5RWaBV"  # test data
        # shareID = "WZys1ZoW" # test data
        workDir = "C:\\Users\\patwnag\\Desktop\\"
        tdm = TreeDataManager(workDir)

        # --------------------------------------------------
        await tdm.retrieveCurrentTreeDataRemote_async(shareID)
        treeData_remote_current = tdm.getCurrentTreeDataRemote()
        print("----------")
        print("current")
        print("----------")
        print(treeData_remote_current)
        print()

        # --------------------------------------------------
        tdm.loadPreviousTreeDataRemote()
        treeData_remote_previous = tdm.getPreviousTreeDataRemote()
        print("----------")
        print("previous")
        print("----------")
        print(treeData_remote_previous)
        print()

        # --------------------------------------------------
        tdm.createDiffListForAction()
        diffListTuple = tdm.getDiffForAction()
        print("----------")
        print("diff")
        print("----------")
        print(diffListTuple)
        print()

        # --------------------------------------------------
        daa = DiffActionAgent()
        daa.doDiffAction(tdm)

        # --------------------------------------------------
        tdm.storeCurrentAsPrevious()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())