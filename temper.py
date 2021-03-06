#!/usr/bin/env python3
# encoding: utf-8
# based on https://github.com/padelt/temper-python

import usb
import sys
import struct
import os
import re
import logging

VIDPIDS = [
    (0x0c45, 0x7401),
]
REQ_INT_LEN = 8
ENDPOINT = 0x82
INTERFACE = 1
TIMEOUT = 5000
COMMANDS = {
    'temp': b'\x01\x80\x33\x01\x00\x00\x00\x00',
    'ini1': b'\x01\x82\x77\x01\x00\x00\x00\x00',
    'ini2': b'\x01\x86\xff\x01\x00\x00\x00\x00',
}
IS_PY2 = sys.version[0] == '2'

class TemperDevice(object):
    """
    A TEMPer USB thermometer.
    """
    def __init__(self, device):
        self._device = device
        self._bus = device.bus
        self._ports = getattr(device, 'port_number', None)
        self._scale = 1.0
        self._offset = 0.0
        logging.debug('Found device | Bus:{0} Ports:{1}'.format(self._bus, self._ports))

    def get_ports(self):
        if self._ports:
            return self._ports
        return ''

    def get_bus(self):
        if self._bus:
            return self._bus
        return ''

    def get_temperature(self):
        """
        Get device temperature reading.
        """
        try:
            # Take control of device if required
            if self._device.is_kernel_driver_active:
                logging.debug('Taking control of device on bus {0} ports {1}'.format(self._bus, self._ports))
                for interface in [0, 1]:
                    try:
                        self._device.detach_kernel_driver(interface)
                    except usb.USBError as err:
                        logging.debug(err)
                self._device.reset()
                self._device.set_configuration()

                for interface in [0, 1]:
                    usb.util.claim_interface(self._device, interface)

                self._device.ctrl_transfer(bmRequestType=0x21, bRequest=0x09,
                    wValue=0x0201, wIndex=0x00, data_or_wLength='\x01\x01',
                    timeout=TIMEOUT)
            # Get temperature
            self._control_transfer(COMMANDS['temp'])
            self._interrupt_read()
            self._control_transfer(COMMANDS['ini1'])
            self._interrupt_read()
            self._control_transfer(COMMANDS['ini2'])
            self._interrupt_read()
            self._interrupt_read()
            self._control_transfer(COMMANDS['temp'])
            data = self._interrupt_read()
        except usb.USBError as err:
            if "insufficient permissions" in str(err):
                raise Exception("Permission problem accessing USB. Did you install the udev rule and replug the device?")
            else:
                logging.error(err)
                raise
        # Interpret device response
        if IS_PY2:
            data_s = b"".join([chr(byte) for byte in data])
        else:
            data_s = data.tobytes()
        logging.debug("Response bytes: " + str(data_s)),
        temp_c = (struct.unpack('>h', data_s[4:6])[0])/256.0
        temp_c = temp_c * self._scale + self._offset
        return temp_c

    def _control_transfer(self, data):
        """
        Send device a control request with standard parameters and <data> as
        payload.
        """
        logging.debug('Ctrl transfer: {0}'.format(data))
        self._device.ctrl_transfer(bmRequestType=0x21, bRequest=0x09,
            wValue=0x0200, wIndex=0x01, data_or_wLength=data, timeout=TIMEOUT)

    def _interrupt_read(self):
        """
        Read data from device.
        """
        data = self._device.read(ENDPOINT, REQ_INT_LEN, timeout=TIMEOUT)
        logging.debug('Read data: {0}'.format(data))
        return data


class TemperHandler(object):
    def __init__(self):
        self._devices = []
        for vid, pid in VIDPIDS:
            for device in usb.core.find(find_all=True, idVendor=vid, idProduct=pid):
                self._devices.append(TemperDevice(device))
        logging.info('Found {0} TEMPer devices'.format(len(self._devices)))

    def get_devices(self):
        return self._devices


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    if usb.__version__ != "1.0.0":
        sys.stderr.write("Unsupported pyusb version: %s\n" % usb.__version__)
    if not "COLLECTD_HOSTNAME" in os.environ:
        os.environ["COLLECTD_HOSTNAME"] = "localhost"
    th = TemperHandler()
    devs = th.get_devices()
    for i, dev in enumerate(devs):
        print("PUTVAL "+os.environ["COLLECTD_HOSTNAME"]+"/temper-"+str(i)+"/temperature N:"+str(dev.get_temperature()))
