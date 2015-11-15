#!/usr/bin/env python
# encoding: utf-8
# based on https://github.com/padelt/temper-python

import usb
import sys
import struct
import os
import re
import logging

VIDPIDS = [
    (0x0c45L, 0x7401L),
]
REQ_INT_LEN = 8
ENDPOINT = 0x82
INTERFACE = 1
TIMEOUT = 5000
COMMANDS = {
    'temp': '\x01\x80\x33\x01\x00\x00\x00\x00',
    'ini1': '\x01\x82\x77\x01\x00\x00\x00\x00',
    'ini2': '\x01\x86\xff\x01\x00\x00\x00\x00',
}
LOGGER = logging.getLogger(__name__)

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
        LOGGER.debug('Found device | Bus:{0} Ports:{1}'.format(self._bus, self._ports))

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
                LOGGER.debug('Taking control of device on bus {0} ports '
                    '{1}'.format(self._bus, self._ports))
                for interface in [0, 1]:
                    try:
                        self._device.detach_kernel_driver(interface)
                    except usb.USBError as err:
                        LOGGER.debug(err)
                self._device.set_configuration()
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
            self._device.reset()
        except usb.USBError as err:
            # Catch the permissions exception and add our message
            if "not permitted" in str(err):
                raise Exception(
                    "Permission problem accessing USB. "
                    "Maybe I need to run as root?")
            else:
                LOGGER.error(err)
                raise
        # Interpret device response
        data_s = "".join([chr(byte) for byte in data])
        temp_c = 125.0/32000.0*(struct.unpack('>h', data_s[2:4])[0])
        temp_c = temp_c * self._scale + self._offset
        return temp_c

    def _control_transfer(self, data):
        """
        Send device a control request with standard parameters and <data> as
        payload.
        """
        LOGGER.debug('Ctrl transfer: {0}'.format(data))
        self._device.ctrl_transfer(bmRequestType=0x21, bRequest=0x09,
            wValue=0x0200, wIndex=0x01, data_or_wLength=data, timeout=TIMEOUT)

    def _interrupt_read(self):
        """
        Read data from device.
        """
        data = self._device.read(ENDPOINT, REQ_INT_LEN, interface=INTERFACE, timeout=TIMEOUT)
        LOGGER.debug('Read data: {0}'.format(data))
        return data


class TemperHandler(object):
    def __init__(self):
        self._devices = []
        for vid, pid in VIDPIDS:
            for device in usb.core.find(find_all=True, idVendor=vid, idProduct=pid):
                # print(str(device))
                self._devices.append(TemperDevice(device))
	LOGGER.info('Found {0} TEMPer devices'.format(len(self._devices)))

    def get_devices(self):
        return self._devices


if __name__ == '__main__':
    th = TemperHandler()
    devs = th.get_devices()
    for i, dev in enumerate(devs):
        print(str(dev.get_temperature()))
