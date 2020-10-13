import asyncio
import json
from RemoteTreeDataManager import RemoteTreeDataManager
from DiffActionAgent import DiffActionAgent


class Main:

    async def main(self):
        shareID = "klUReHe5"  # test data HW TOPNO2
        # shareID = "OXrq5h3g"  # test data HW TOPNO3
        # shareID = "WjCz6B10"  # test data HW NBNO3
        workDir = "C:\\Users\\patwnag\\Desktop\\" # HW TOPNO2
        # workDir = "C:\\Users\\patwang\\Desktop\\"  # HW NBNO3, HW TOPNO3
        rtdm = RemoteTreeDataManager(workDir, shareID)

        # --------------------------------------------------
        await rtdm.retrieveCurrentRemoteTreeData_async()
        treeData_remote_current = rtdm.getCurrentTreeDataRemote()
        print("----------")
        print("current")
        print("----------")
        # print(treeData_remote_current)
        print(json.dumps(treeData_remote_current, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        rtdm.loadPreviousTreeDataRemote()
        treeData_remote_previous = rtdm.getPreviousTreeDataRemote()
        print("----------")
        print("previous")
        print("----------")
        # print(treeData_remote_previous)
        print(json.dumps(treeData_remote_previous, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        rtdm.createDiffListForAction()
        diffListTuple = rtdm.getDiffForAction()
        print("----------")
        print("diff")
        print("----------")
        print(json.dumps(diffListTuple, indent=4, ensure_ascii=False))  # for debug only
        print()

        # --------------------------------------------------
        daa = DiffActionAgent()
        daa.doDiffAction(rtdm)

        # --------------------------------------------------
        rtdm.storeCurrentAsPrevious()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Main().main())
