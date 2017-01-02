# Install

Python 3:

```shell
sudo apt-get install python3-usb python3-pip
sudo pip3 install -r requirements.txt
sudo cp 60-temper.rules /lib/udev/rules.d/
sudo ln -s `pwd`/temper.py /usr/local/bin/temper.py
```

Python 2:

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
  Interval 60
  Exec "your_username:input" "/usr/local/bin/temper.py"
</Plugin>
```

```shell
sudo service collectd restart
```

## graph example

```
COLLECTD=/var/lib/collectd/rrd/raspberrypi/

rrdtool graph graphs/1d_temp.png \
  --start -86400 \
  --end now \
  -w 1200 -h 400 \
  -a PNG \
  --slope-mode \
  --title "temp (1 day)" \
  --watermark "$DATE" \
  --vertical-label "Temperature (C)" \
  --x-grid HOUR:1:HOUR:6:HOUR:1:0:%H \
  DEF:temp1=$COLLECTD/temper-0/temperature.rrd:value:AVERAGE \
  LINE1:temp1#ff0000:"temper" \
  > /dev/null

rrdtool graph 1m_temp.png \
  --start -2592000 \
  --end now \
  -w 1200 -h 400 \
  -a PNG \
  --slope-mode \
  --title "temp (1 month)" \
  --watermark "$DATE" \
  --vertical-label "Temperature (C)" \
  --x-grid HOUR:4:WEEK:1:DAY:1:0:%d \
  DEF:temp1=$COLLECTD/temper-0/temperature.rrd:value:AVERAGE \
  LINE1:temp1#ff0000:"temper" \
  > /dev/null
```
