# Install

```shell
sudo apt-get install python-usb python-pip
sudo pip install -I pyusb==1.0.0b1
sudo cp 60-temper.rules /lib/udev/rules.d/
sudo ln -s `pwd`/temper.py /usr/local/bin/temper.py
```

## collectd.conf

```
LoadPlugin exec
<Plugin exec>
  Exec your_username "/usr/local/bin/temper.py"
</Plugin>
```

```shell
sudo service collectd restart
```
