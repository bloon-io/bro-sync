## Install Python 3.6+ in Ubuntu 16.04

Install required dependencies first

```
$ sudo apt-get update
$ sudo apt-get -y install zlib1g-dev build-essential checkinstall \
    libreadline-gplv2-dev libncursesw5-dev libssl-dev \
    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev
```

Download source code from Python official site & unzip

```
$ wget https://www.python.org/ftp/python/3.6.9/Python-3.6.9.tgz
$ tar zxfv Python-3.6.9.tgz
```

Build and install Python 3.6.9

```
$ cd Python-3.6.9
$ ./configure
$ make
$ make install
```

P.S. You can change the version "3.6.9" above to other ones. Choose the version string you want in [this official FTP page][1].

[1]: https://www.python.org/ftp/python
