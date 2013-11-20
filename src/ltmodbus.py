#!/usr/bin/env python
# -*- coding:utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# Copyright (C) 2013 Yaacov Zamir <kobi.zamir@gmail.com>
# Author: Yaacov Zamir (2013)

""" ltmodbus.py

A little modbus sub protocol for a data logger
"""

import os
import sys

from struct import pack,unpack
import socket

try:
    from serial import Serial
except:
    # no serial comunication
    pass

class LTModbus():
    """ interface for a little modbus module
    
    this module read and write paramters:
        parameters are two registers interpeted as floats, 
        the address of a paramters is addr/2 and the count of paramters is 
        count/2.
    """
    
    def send(self, msg, answer_length):
        """ send a message and wait for ans_length chars
        
        msg -- the messeg to send
        answer_length -- wait for ans_length chars
        
        return -- the answer chars
        """
        
        raise Exception("LTModbus::send - Not implementd")
    
    def get_par(self, unit, addr, count):
        """ get input registers from a modbus unit

        unit -- modbus unit number
        addr -- start addres [par addr = modbus addr / 2]
        count -- number of registers to read [par count = modbus count / 2]
        """
        
        # update addr and count
        addr = addr*2 - 1
        count *= 2
        
        ans = []
        command = 4
        answer_length = 3 + count * 2
        
        # build modbus request
        msg = pack('>2B2H', unit, command, addr, count)
        
        # wait for answer (do not check CRC)
        replay = self.send(msg, answer_length)
        
        # if we have and answer, get the registers content
        if replay and len(replay) == answer_length:
            ans = unpack(">%df" % (count / 2), replay[3:])
        
        return ans
    
    def set_par(self, unit, addr, count, regs):
        """ set input registers from in a modbus unit

        unit -- modbus unit number
        addr -- start addres [par addr = modbus addr / 2]
        count -- number of registers to read [par count = modbus count / 2]
        regs -- an array of data to write
        """
        
        # update addr and count
        addr = addr*2 - 1
        count *= 2
        
        ans = [0, 0,]
        command = 0x10
        answer_length = 6
        
        # build modbus request
        msg = pack('>2B2HB%df' % len(regs), unit, command, addr, 
            count, count * 2, *regs)
        
        # wait for answer (do not check CRC)
        replay = self.send(msg, answer_length)
        
        # if we have and answer, get the addr and number of registers
        if len(replay) == answer_length:
            ans = unpack(">2H", replay[2:])
        
        return ans

class LTModbusSerial(Serial, LTModbus):
    """ a little modbus module using serial bus
    """
    
    def __init__(self, *arguments, **keywords):
        # init the serial interface
        Serial.__init__(self, *arguments, **keywords)
        
        # init the cache
        self.ttl = 0
        self.cache = {}
    
    def swap_bytes(self, word_val):
        """ swap lsb and msb of a word """
        msb = word_val >> 8
        lsb = word_val % 256
        return (lsb << 8) + msb
    
    def _calc_crc16(self, data):
        """ calculate 16 bit CRC of a datagram """
        crc = 0xFFFF
        for i in data:
            crc = crc ^ ord(i)
            for j in xrange(8):
                tmp = crc & 1
                crc = crc >> 1
                if tmp:
                    crc = crc ^ 0xA001

        return pack('>H', self.swap_bytes(crc))
    
    def send(self, msg, answer_length):
        """ send a message and wait for ans_length chars
        
        msg -- the messeg to send
        answer_length -- wait for ans_length chars
        
        return -- the answer chars
        """
        
        # make sure no leftovers in buffers
        self.flushInput()
        self.flushOutput()
        
        # calc outgoing CRC
        msg = msg + self._calc_crc16(msg)
        
        # write data to unit
        self.write(msg)
        
        # wait for answer and the 2 crc bytes(do not check CRC)
        try:
            replay = self.read(answer_length + 2)
        except Exception:
            replay = []
        
        return replay[:-2]
    
    def get_par(self, unit, addr, count):
        """ get input registers from a modbus unit
        
        cached version of the get registers function
        
        unit -- modbus unit number
        addr -- start addres [par addr = modbus addr / 2]
        count -- number of registers to read [par count = modbus count / 2]
        """
        
        # no cache
        if self.ttl == 0:
            return LTModbus.get_par(self, unit, addr, count)
        
        # use cache
        now = time.time()
        key = "%d-%d-%d" % (unit, addr, count)
        try:
            # check key
            values, last_update = self.cache[key]
            if (now - last_update) > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            # get fresh values
            values = LTModbus.get_par(self, unit, addr, count)
            self.cache[key] = (values, now)
        
        return values

class LTModbusTCP(LTModbus):
    """ a little modbus module using TCP/IP
    """
    
    def __init__(self, tcp_ip):
        # defults modbus port
        self.tcp_port = 502
        
        # open socket
        self.ip = tcp_ip
    
    def open(self):
        """ open socket """
        
        # open socket
        try:
            self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.soc.settimeout(2)
            self.soc.connect((self.ip, self.tcp_port))
        except socket.error:
            raise Exception("Can't connect to unit")
        
    def close(self):
        """ open socket """
        
        self.soc.close()
        
    def send(self, msg, answer_length):
        """ send a message and wait for ans_length chars
        
        msg -- the messeg to send
        answer_length -- wait for ans_length chars
        
        return -- the answer chars
        """
        
        # send data using tcp
        message = pack(">3H", 1, 0, len(msg)) + msg
        
        self.soc.send(message)
        replay = self.soc.recv(answer_length + 6)
        
        return replay[6:]

