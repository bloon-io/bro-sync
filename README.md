## BLOON Read-Only Sync ##

To synchronize the folder you shared through a BLOON sharelink.

The following line shows how to get an ID from a sharelink:
```
https://www.bloon.io/share/[a sharelink ID]/
```

How to get a shearlink?
See [https://www.bloon.io/help/sharelinks][1]

## Dependencies ##

* Python 3.5+
* [websockets][2]
* [sqlitedict][3]

## Installation ##

```
$ pip3 install -r requirements.txt
```

Or you can use [virtual environment][4]
```
$ virtualenv venv
$ source ./venv/bin/activate
$ pip install -r requirements.txt
```

## Usage ##

```
usage: main.py [-h] [-s] [-q] [--detail] SHARE_ID WORK_DIR

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

## Example ##

To synchronize once
```
$ python3 ./main.py eXaMpLE77 /home/patrick/myBroSyncHome
```

To start synchronizing as a non-stop service
```
$ python3 ./main.py eXaMpLE77 ../myBroSyncHome -s
```

To start service in background
```
$ python3 ./main.py --serice eXaMpLE77 ../myBroSyncHome &
```

To stop bro-sync service, press "Ctrl + Break" or kill the process.

For example, you can kill the bro-sync service process which runs in background with the sharelink ID "eXaMpLE88" in this way
```
sid="eXaMpLE88"; kill -9 $(ps aux | grep -v grep | grep "$sid" | awk '{print $2}')
```

[1]: https://www.bloon.io/help/sharelinks
[2]: https://pypi.org/project/websockets/
[3]: https://pypi.org/project/sqlitedict/
[4]: https://docs.python-guide.org/dev/virtualenvs/
