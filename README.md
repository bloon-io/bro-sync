### [English][100], [繁體中文][101]

## BLOON Read-Only Sync

A command-line tool for synchronizing and batch downloading the folder you shared through a BLOON sharelink.

"Read-Only Sync" means download only; no changes in local will be synchronized to other devices.

The following line shows how to get an ID from a sharelink:

```
https://www.bloon.io/share/[a sharelink ID]/
```

How to get a sharelink? See [https://www.bloon.io/help/sharelinks][1]

## Dependencies

- Mac / Linux / Windows
- Python 3.7+
- [websockets][2]
- [sqlitedict][3]

The default python3 version in Ubuntu 16.04 is 3.5.2. You can see [this page][102] to know how to install Python 3.7+ in Ubuntu 16.04.

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

usage: bro-sync.py [-h] (-s WORK_DIR | -t dir_path) [-q] [--service] [--detail] SHARE_ID

  To synchronize the folder you shared through a BLOON sharelink.

  The following line shows how to get an ID from a sharelink:
  https://www.bloon.io/share/[a sharelink ID]/

  How to get a sharelink?
  See https://www.bloon.io/help/sharelinks

positional arguments:
  SHARE_ID                          A BLOON sharelink ID of your folder.

options:
  -h, --help                        show this help message and exit
  -s, --sync WORK_DIR               start and keep syncing
  -t, --no-stash-transfer dir_path  wait and receive file directly without staging in bloon
  -q, --quiet                       run quietly, show nothing on screen
  --service                         start and keep syncing
  --detail                          show more details on screen
```

## Example

To synchronize once (batch download the contents of this folder)

```
$ python3 ./bro-sync.py eXaMpLE77 -s /home/patrick/myBroSyncHome
```

To start synchronizing as a non-stop service

```
$ python3 ./bro-sync.py eXaMpLE77 -s ../myBroSyncHome --service
```

To start service in background

```
$ python3 ./bro-sync.py --service -s eXaMpLE77 ../myBroSyncHome &
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
[102]: https://github.com/bloon-io/bro-sync/blob/master/misc/ubuntu16.04_install_py3.7.md
