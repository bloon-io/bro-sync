import asyncio
from TreeDataManager import TreeDataManager

class Main:
    async def main(self):
        shareID = "JJ5RWaBV"  # test data
        # shareID = "WZys1ZoW" # test data
        workDir = "C:\\Users\\patwnag\\Desktop\\"
        tdm = TreeDataManager(workDir)

        # --------------------------------------------------
        await tdm.retrieveTreeDataRemote_async(shareID)
        treeData_remote_current = tdm.getCurrentTreeDataRemote()
        print("----------")
        print("current")
        print("----------")
        print(treeData_remote_current)
        print()

        # --------------------------------------------------
        tdm.loadTreeDataRemote()
        treeData_remote_previous = tdm.getPreviousTreeDataRemote()
        print("----------")
        print("previous")
        print("----------")
        print(treeData_remote_previous)
        print()

        # --------------------------------------------------
        diffListTuple = tdm.createDiffListForAction(
            treeData_remote_current, treeData_remote_previous)
        print("----------")
        print("diff")
        print("----------")
        print(diffListTuple)
        print()

        # --------------------------------------------------
        tdm.storeTreeDataRemote(treeData_remote_current)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())