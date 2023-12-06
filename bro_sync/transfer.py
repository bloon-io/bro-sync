import logging
import websockets
import os
import pathlib
from bro_sync.ctx import Ctx

log = logging.getLogger("bro-sync")

class WireFlag:
    FILE_BLOCK_FLAG = 1
    REQUEST_BLOCK_FLAG = 3
    FILE_TRANSFER_FINISH_FLAG = 7
    FILE_TRANSFER_FINISH_ACK = 8
    TO_BLINK_REGISTER_FLAG = 51
    FROM_BLINK_REGISTER_ACK = 61
    FROM_BLINK_DISCONNECT_FLAG = 99

class BlinkWire:
    
    def __init__(self, addr, messageHandler):
        self.blinkUrl = "wss://" + addr + Ctx.BLOON_BLINK_URL_SUFFIX
        self.messageHandler = messageHandler

    async def connect(self, wirePortID, pairWirePortID):
        try:
            async with websockets.connect(self.blinkUrl, ssl=Ctx.API_WSS_SSL_CONTEXT) as wss:
                self.wss = wss
                self.isConnected = True
                await self.sendRegisterMsg(wirePortID + ";" + pairWirePortID)
                while self.isConnected:
                    recMsg = await self.wss.recv()
                    await self.messageHandler(recMsg)

        except BaseException as e:
            self.isConnected = False
            print("")
            log.warning("exception reason: [" + str(e) + "]")

    def isReady(self):
        return self.isConnected
    
    async def stopConnect(self):
        self.isConnected = False
        await self.wss.close()
        
    async def sendTransferFinshAck(self):
        wireMsgBytes = bytearray()
        wireMsgBytes.append(WireFlag.FILE_TRANSFER_FINISH_ACK)
        await self.sendData(wireMsgBytes)

    async def sendRegisterMsg(self, wirePortIDStr):
        wireMsgBytes = bytearray()
        wireMsgBytes.append(WireFlag.TO_BLINK_REGISTER_FLAG)
        wireMsgBytes.extend(wirePortIDStr.encode('utf-8'))
        await self.sendData(wireMsgBytes)

    async def sendData(self, data):
        if self.isConnected:
            await self.wss.send(data)

class FileTransfer:

    FILE_BLOCK_SIZE = int(4 * 1024)
    REQUEST_BLOCK_COUNT = int(2048)

    def __init__(self, wireData, workDir):
        self.fileName = wireData["fileName"]
        self.fileSize = wireData["fileSize"]
        self.fileID = wireData["fileID"]
        self.wirePortID = wireData["wirePortID"]
        self.pairWirePortID = wireData["pairWirePortID"]
        self.blinkAddress = wireData["blinkAddress"]
        self.workDir = workDir
        self.targetFile = None

        # for file transfer args
        self.startBlockIndex = int(0)
        self.endBlockIndex = int((self.fileSize + FileTransfer.FILE_BLOCK_SIZE - 1) / FileTransfer.FILE_BLOCK_SIZE)
        self.nextBlockIndex = int(0)
        self.requestBlockIndex = int(0)

    async def start_receive_file_async(self):
        self.wire = BlinkWire(self.blinkAddress, self.handle_message_async)
        await self.wire.connect(self.wirePortID, self.pairWirePortID)
        if self.nextBlockIndex == self.endBlockIndex:
            return True
        elif self.nextBlockIndex > 0:
            print("")
            return False
        return False
    
    async def handle_message_async(self, message):
        flag = message[0]
        if flag == WireFlag.FROM_BLINK_REGISTER_ACK:
            log.debug("wire is connected..")
            await self._send_request_async()
        elif flag == WireFlag.FROM_BLINK_DISCONNECT_FLAG:
            await self.wire.stopConnect()
        elif flag == WireFlag.FILE_TRANSFER_FINISH_FLAG:
            await self.wire.sendTransferFinshAck()
        elif flag == WireFlag.FILE_BLOCK_FLAG:
            if not self._save_block_gram(message):
                await self.wire.stopConnect()
            elif (self.requestBlockIndex - self.nextBlockIndex) < (self.REQUEST_BLOCK_COUNT / 2):
                await self._send_request_async()
            
    def _open_target_file(self):
        folderPath = os.path.abspath(self.workDir)
        if not os.path.exists(folderPath):
            log.info("[ACTION] mkdir -p: [" + folderPath + "]")
            os.makedirs(folderPath, exist_ok=True)
        filePath = os.path.join(folderPath, self.fileName)
        baseName = pathlib.Path(filePath).stem
        suffix = pathlib.Path(filePath).suffix
        index = 0
        while os.path.exists(filePath):
            index += 1
            self.fileName = "{0} ({1}){2}".format(baseName, index, suffix)
            filePath = os.path.join(folderPath, self.fileName)
        try:
            self.targetFile = open(filePath, "wb")
            return True
        except BaseException as e:
            log.warning("open file failed. reason: [" + str(e) + "]")
            return False

    def _save_block_gram(self, blockPacket):
        # Wire blockgram packet protocol :
        #      -  1 bytes : flag
        #      -  4 bytes : packet size = 36 + 8 + x
        #      - 36 bytes : file uuid
        #      -  8 bytes : block index
        #      -  x bytes : block raw data
        indexBytes = blockPacket[41:49]
        blockBytes = blockPacket[49:]

        blockIndex = int.from_bytes(indexBytes, byteorder='big', signed=True)
        if self.nextBlockIndex != blockIndex:
            return False
        if not self.targetFile:
            if not self._open_target_file():
                return False

        try:
            self.targetFile.write(blockBytes)
        except BaseException as e:
            print("")
            log.warning("write file failed. reason: [" + str(e) + "]")
            return False
        
        self.nextBlockIndex = blockIndex + 1
        if blockIndex % 100 == 0:
            recMBytes = self.nextBlockIndex * FileTransfer.FILE_BLOCK_SIZE / 1024 / 1024
            progress = self.nextBlockIndex * 100 / self.endBlockIndex
            outstr = "{0}\t\t\t {1:8.2f}MB ({2:3.1f}%)".format(self.fileName, recMBytes, progress)
            print(outstr, end='\r')
        
        if self.nextBlockIndex == self.endBlockIndex:
            self.targetFile.close()
            recMBytes = self.fileSize / 1024 / 1024
            outstr = "{0}\t\t\t {1:8.2f}MB ({2:3.1f}%)".format(self.fileName, recMBytes, 100)
            print(outstr)
        return True

    async def _send_request_async(self):
        self.requestBlockIndex = self.nextBlockIndex + self.REQUEST_BLOCK_COUNT
        if self.requestBlockIndex > self.endBlockIndex:
            self.requestBlockIndex = self.endBlockIndex
        
        # protocol
        #   - 1 bytes : flag
        #   - 1 bytes : size
        #   - 36 bytes : file uuid
        #   -  8 bytes : start block index
        #   -  8 bytes : end block index
        indexBytes = bytearray()
        indexBytes.append(WireFlag.REQUEST_BLOCK_FLAG)
        indexBytes.append(52)
        indexBytes.extend(self.fileID.encode('utf-8'))
        indexBytes.extend(self.nextBlockIndex.to_bytes(8, byteorder='big', signed=True))
        indexBytes.extend(self.requestBlockIndex.to_bytes(8, byteorder='big', signed=True))
        await self.wire.sendData(indexBytes)
