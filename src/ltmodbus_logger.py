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

""" ltmodbus_logger.py

A modbus RS485 little trend reader
"""

import os
import sys
import time
import calendar
import datetime
import argparse

try:
    import sqlite3
except:
    pass

from ltmodbus import LTModbusTCP, LTModbusSerial

SQL_DATA_TABLE = '''create table if not exists data (
            timestamp integer primary key, time text,
            p01 numeric, p02 numeric, p03 numeric, p04 numeric, p05 numeric,
            p06 numeric, p07 numeric, p08 numeric, p09 numeric, p10 numeric,
            p11 numeric, p12 numeric, p13 numeric, p14 numeric, p15 numeric,
            p16 numeric, p17 numeric, p18 numeric);'''
CSV_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
SQL_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.000000"

class LTModbusLogger():
    """ a little modbus module
    
    a little modbus module with functions to read a data logger
    """
    
    def __init__(self, soc):
        self.soc = soc
        self.unit = 31
    
    def set_date(self,d,m,y,h,M,s):
        """ set reading frame to date
        """
        
        self.soc.set_par(self.unit, 5941, 6, [d,m,y,h,M,s])
        
    def inc_date(self):
        """ set reading frame to next frame
        """
        
        self.soc.set_par(self.unit, 5940, 1, [0,])
    
    def read_points(self):
        """ read ftrend points
        """
        
        # points are in pars 5975 ...
        return self.soc.get_par(self.unit, 5975, 18)
        
    def read_data(self):
        """ read current frame date and data
        """
        
        # data is in pars 5951 ...
        data = self.soc.get_par(self.unit, 5951, 18)
        
        # get timestamp
        d,m,y,h,M,s = self.soc.get_par(self.unit, 5941, 6)
        time_tuple = map(int, (y,m,d,h,M,s,0,0,0))
        
        try:
            timestamp = calendar.timegm(time_tuple)
        except:
            timestamp = 0
        
        return (timestamp,) + data

def dump_line(f, c, csv_line, sql_line):
    """ dump data line to data-base, csv-file and stdout
    """
    
    print csv_line
    
    try:
        if f:
            f.write("%s\n" % csv_line)
        if c:
            sql = '''insert into data values (%s);''' % sql_line
            c.execute(sql)
    except Exception:
        print "Err: %s" % "can't write to file"

def main():
    """ get user arguments and run the modbus repeater
    """
    
    # command line parser
    parser = argparse.ArgumentParser(description='LT-Modbus trend reader.')
    
    parser.add_argument('-u', dest='unit',
                       type=int, default=31,
                       help='unit number (default: 31)')
    parser.add_argument('-b', dest='baudrate',
                       type=int, default=4800,
                       help='serial port baudrate (default: 4800)')
    parser.add_argument('-p', dest='parity',
                       type=str, default='E',
                       help='serial port parity (default: E)')
    parser.add_argument('-c', dest='port',
                       type=str, default='COM1',
                       help='serial port com-port')
    parser.add_argument('-i', dest='ip',
                       type=str, default='',
                       help='unit ip, for TCP/IP comunication')
    parser.add_argument('-t', dest='time_str',
                       type=str, default='',
                       help='time in "dd/mm/yyyy hh:mm:ss" fromat')
    parser.add_argument('-n', dest='num',
                       type=int, default=20,
                       help='number of frames to read (default: 20)')
    parser.add_argument('-f', dest='filename',
                       type=str, default='',
                       help='.csv file name or .sqlite db')
                       
    args = parser.parse_args()
    
    # open serial/tcp port
    if args.ip != '':
        soc = LTModbusTCP(args.ip)
        soc.open()
    else:
        soc = LTModbusSerial(port=args.port, 
            baudrate=args.baudrate, bytesize=8, parity=args.parity, stopbits=1)
        soc.timeout = 1.5
    
    # create comunication object
    ser = LTModbusLogger(soc)
    
    # set unit number
    ser.unit = args.unit
    
    # set timestamp
    try:
        # try to parse the date string
        struct_time = time.strptime(args.time_str, "%d/%m/%Y %H:%M:%S")
        y,m,d,h,M,s,wd,yd,tz = struct_time
    except Exception:
        # get a starting timestamp (now - one hour)
        now = datetime.datetime.now()
        now -= datetime.timedelta(hours=1)
        y,m,d,h,M,s,wd,yd,tz = now.timetuple()
    
    # open csv file
    if args.filename and args.filename.endswith('.csv'):
        f = open(args.filename,'wb')
    else:
        f = None
    
    # open sqlite db
    if args.filename and args.filename.endswith('.sqlite'):
        conn = sqlite3.connect(args.filename)
        c = conn.cursor()
        
        sql = SQL_DATA_TABLE
        c.execute(sql)
        conn.commit()
    else:
        c = None
    
    # get points
    points = ser.read_points()
    print "points: timestamp, %s" % ",".join(["P%02d " % p for p in points])
    
    # read N frames starting from timestamp
    ser.set_date(d,m,y,h,M,s)
    
    # read data
    for i in range(args.num):
        # get new data line
        frame = ser.read_data()
        ser.inc_date()
        
        # if we have valid line 
        if frame[0] != 0:
            frame_time_str_csv = time.strftime(CSV_DATETIME_FORMAT, time.gmtime(frame[0]))
            frame_time_str_sql = time.strftime(SQL_DATETIME_FORMAT, time.gmtime(frame[0]))
            
            csv_line = "%s,%s" % (frame_time_str_csv, ",".join(["%.02f" % p for p in frame[1:]]))
            sql_line = "%d,'%s',%s" % (frame[0], frame_time_str_sql, ",".join(["%.02f" % p for p in frame[1:]]))
            dump_line(f, c, csv_line, sql_line)
            
    # close open files
    if f:
        f.close()
    if c:
        conn.commit()
    
    # close socket
    soc.close()
    
if __name__ == '__main__':
    main()

