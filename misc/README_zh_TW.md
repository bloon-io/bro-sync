### [English][100], [繁體中文][101]

## BLOON Read-Only Sync

命令列工具，讓你可以同步、批次下載經由 BLOON 分享連結所分享的資料夾。

「Read-Only Sync ( 唯讀同步 )」意思是僅下載，而不會將本地修改同步到其他裝置上。

以下顯示如何取得「sharelink ID」

```
https://www.bloon.io/share/[a sharelink ID]/
```

如何建立分享連結？請參考：[https://www.bloon.io/help/sharelinks][1]

## 相依套件

- Mac / Linux / Windows
- Python 3.7+
- [websockets][2]
- [sqlitedict][3]

Ubuntu 16.04 預設的 python3 版本是 3.5.2，你可以參考[此頁][102]說明，在 Ubuntu 16.04 上正確安裝 Python 3.7 ( 以上 ) 版本。

## 安裝方式

```
$ git clone https://github.com/bloon-io/bro-sync.git
$ cd bro-sync
$ pip3 install -r requirements.txt
```

## 使用方式

```
$ cd bro-sync
$ python3 ./bro-sync.py

usage: bro-sync.py [-h] [-s] [-q] [--detail] SHARE_ID WORK_DIR

  To synchronize a folder you shared through a BLOON sharelink.

  The following line shows how to get an ID from a sharelink:
  https://www.bloon.io/share/[a sharelink ID]/

  How to get a sharelink?
  See https://www.bloon.io/help/sharelinks

positional arguments:
  SHARE_ID       A BLOON sharelink ID of your folder.
  WORK_DIR       The place you want to put your sync. folder.

optional arguments:
  -h, --help     show this help message and exit
  -s, --service  start and keep syncing
  -q, --quiet    run quietly, show nothing on screen
  --detail       show more details on screen
```

## 使用範例

僅進行一次同步 ( 即資料夾內容批次下載 )：

```
$ python3 ./bro-sync.py eXaMpLE77 /home/patrick/myBroSyncHome
```

將 bro-sync 啟動為服務，持續監測並同步其他裝置上的檔案異動：

```
$ python3 ./bro-sync.py eXaMpLE77 ../myBroSyncHome --service
```

讓 bro-sync 服務在背景執行：

```
$ python3 ./bro-sync.py -s eXaMpLE77 ../myBroSyncHome &
```

要停止 bro-sync 服務，你可以按下「Ctrl + Break」中斷程式 ( 在非背景執行情況下 )，或是砍除應用程式。

舉例來說，如果 bro-sync 在背景執行，並且其 sharelink ID 是「eXaMpLE88」，你可以使用以下簡單的 shell script 挑出其 PID 並砍除程式：

```
sid="eXaMpLE88"; kill -9 $(ps aux | grep -v grep | grep "$sid" | awk '{print $2}')
```

[1]: https://www.bloon.io/help/sharelinks
[2]: https://pypi.org/project/websockets/
[3]: https://pypi.org/project/sqlitedict/
[100]: https://github.com/bloon-io/bro-sync/blob/master/README.md
[101]: https://github.com/bloon-io/bro-sync/blob/master/misc/README_zh_TW.md
[102]: https://github.com/bloon-io/bro-sync/blob/master/misc/ubuntu16.04_install_py3.7.md
