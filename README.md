# Install

```shell
sudo apt-get install python-usb python-pip
sudo pip install -r requirements.txt
sudo cp 60-temper.rules /lib/udev/rules.d/
sudo ln -s `pwd`/temper.py /usr/local/bin/temper.py
```

## collectd.conf

```
LoadPlugin exec
<Plugin exec>
  Exec "your_username:input" "/usr/local/bin/temper.py"
</Plugin>
```

```shell
sudo service collectd restart
```
