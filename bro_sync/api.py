import json
import inspect
import logging

log = logging.getLogger("bro-sync")


class WssApiCaller:

    def __init__(self, wss):
        self.wss = wss

    """
    The purpose of this code: "inspect.getframeinfo(inspect.currentframe()).function[:-6]"
    is for getting current function name (by using reflaction) and then remove the end string "_async".
    """
    async def getFoldersMin_async(self, params):
        return await self._wssCall_async(inspect.getframeinfo(inspect.currentframe()).function[:-6], params)

    async def getCardsMin_async(self, params):
        return await self._wssCall_async(inspect.getframeinfo(inspect.currentframe()).function[:-6], params)

    async def getShareInfo_async(self, params):
        return await self._wssCall_async(inspect.getframeinfo(inspect.currentframe()).function[:-6], params)

    async def _wssCall_async(self, funcName, params):
        params["token"] = None
        inData = {
            "func_name": funcName, "cbID": "",
            "params": params
        }
        reqStr = json.dumps(inData)
        await self.wss.send(reqStr)
        resStr = await self.wss.recv()
        outData = json.loads(resStr)
        return outData
