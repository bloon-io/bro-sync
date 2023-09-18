import re
import hashlib
from sqlitedict import SqliteDict

class Utils:
    @staticmethod
    def getAvailableFileBaseName(baseName, isEmptyExt):
        fileName = re.sub( r'[' + re.escape('\\/:*?\"<>|') + r']', '_', baseName).strip()
        if fileName.lower() == "con":
            # windows limitation, file name can not be 'con'
            fileName = fileName + '_'
        if isEmptyExt and fileName.endswith('.'):
            fileName = re.sub( r'\.+$', '_', fileName); 
        return fileName

    @staticmethod
    def getFileName(baseName, extension, index):
        dotExtension = '.' + extension if extension else ''
        return baseName + dotExtension if index == 0 else baseName + ' (' + str(index) + ')' + dotExtension

    @staticmethod
    def getFileChecksum(filePath):
        sha = hashlib.sha1()
        with open(filePath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha.update(chunk)
        return sha.hexdigest()

    @staticmethod
    def show_db_content(db_file_path):
        print("---------- ctx ----------")
        with SqliteDict(db_file_path, tablename="ctx") as ctx_db:
            for key, value in ctx_db.items():
                print(f'Key: {key}, Value: {value}')

        print("---------- file_dict ----------")
        with SqliteDict(db_file_path, tablename="file_dict") as file_dict_db:
            for key, value in file_dict_db.items():
                print(f'Key: {key}, Value: {value}')
                
        print("---------- folder_set ----------")
        with SqliteDict(db_file_path, tablename="folder_set") as folder_set_db:
            for key, value in folder_set_db.items():
                print(f'Key: {key}, Value: {value}')