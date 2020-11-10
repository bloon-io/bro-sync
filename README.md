### [English][100], [繁體中文][101]

## BLOON Read-Only Sync

To synchronize the folder you shared through a BLOON sharelink.

"Read-Only Sync" means download only, no changes in local will be synchronized to other devices.

The following line shows how to get an ID from a sharelink:

```
https://www.bloon.io/share/[a sharelink ID]/
```

How to get a shearlink? See [https://www.bloon.io/help/sharelinks][1]

## Dependencies

- Mac / Linux / Windows
- Python 3.6+
- [websockets][2]
- [sqlitedict][3]

The default python3 version in Ubuntu 16.04 is 3.5.2. You can see [this page][102] to know how to install Python 3.6+ in Ubuntu 16.04.

## Installation

```
$ git clone https://github.com/bloon-io/bro-sync.git
$ cd bro-sync
$ pip3 install -r requirements.txt
```

## Usage

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

## Example

To synchronize once (batch download the contents of this folder)

```
$ python3 ./bro-sync.py eXaMpLE77 /home/patrick/myBroSyncHome
```

To start synchronizing as a non-stop service

```
$ python3 ./bro-sync.py eXaMpLE77 ../myBroSyncHome --service
```

To start service in background

```
$ python3 ./bro-sync.py -s eXaMpLE77 ../myBroSyncHome &
```

To stop bro-sync service, press "Ctrl + Break" or kill the process.

For example, you can kill the bro-sync service process which runs in background with the sharelink ID "eXaMpLE88" in this way

```
sid="eXaMpLE88"; kill -9 $(ps aux | grep -v grep | grep "$sid" | awk '{print $2}')
```

[1]: https://www.bloon.io/help/sharelinks
[2]: https://pypi.org/project/websockets/
[3]: https://pypi.org/project/sqlitedict/
[100]: https://github.com/bloon-io/bro-sync/blob/master/README.md
[101]: https://github.com/bloon-io/bro-sync/blob/master/misc/README_zh_TW.md
[102]: https://github.com/bloon-io/bro-sync/blob/master/misc/ubuntu16.04_install_py3.6.md
