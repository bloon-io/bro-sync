## [繁體中文][101], [English][100]

## BLOON Read-Only Sync

同步藉由 BLOON 分享連結所分享的資料夾。

以下顯示如何取得「sharelink ID」

```
https://www.bloon.io/share/[a sharelink ID]/
```

如何建立分享連結？請參考：
[https://www.bloon.io/help/sharelinks][1]

## 相依套件

- Python 3.6+
- [websockets][2]
- [sqlitedict][3]

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

  How to get a shearlink?
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

進行一次性的同步：

```
$ python3 ./bro-sync.py eXaMpLE77 /home/patrick/myBroSyncHome
```

將 bro-sync 啟動為服務，持續同步其他裝置上的檔案異動：

```
$ python3 ./bro-sync.py eXaMpLE77 ../myBroSyncHome --service
```

讓 bro-sync 服務在背景執行：

```
$ python3 ./bro-sync.py -s eXaMpLE77 ../myBroSyncHome &
```

要停止 bro-sync 服務，你可以按下「Ctrl + Break」中斷程式 ( 在非背景執行情況下 )，或是砍除應用程式。

舉例來說，如果 bro-sync 服務在背景執行，並且其 sharelink ID 是「eXaMpLE88」，你可以使用以下簡單的 shell script 挑出其 PID 並砍除程式：

```
sid="eXaMpLE88"; kill -9 $(ps aux | grep -v grep | grep "$sid" | awk '{print $2}')
```

[1]: https://www.bloon.io/help/sharelinks
[2]: https://pypi.org/project/websockets/
[3]: https://pypi.org/project/sqlitedict/
[100]: https://github.com/bloon-io/bro-sync/blob/master/README.md
[101]: https://github.com/bloon-io/bro-sync/blob/master/README_zh_TW.md
