import re

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



