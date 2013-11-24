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

import os
import time
import calendar
import thread
import datetime
import os.path as op

from ltmodbus import LTModbusTCP, LTModbusSerial

# csv format
CSV_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

path = op.join(op.dirname(__file__), 'files')

class LTModbusLogger():
    """ a little modbus module
    
    a little modbus module with functions to read a data logger
    """
    
    busy_flag = False
    busy_percent = 0
    run = True
    
    def __init__(self):
        self.soc = None
        self.unit = 31
    
    def open_soc(self, port_info):
        """ try to open Serial port
        """
        try:
            self.soc = LTModbusSerial(
                port=port_info.com, 
                baudrate=port_info.baud, 
                bytesize=port_info.databits, 
                parity=port_info.parity, 
                stopbits=1)
            self.soc.timeout = port_info.timeout
        except Exception, e:
            self.soc = None
            raise

    def set_date(self,d,m,y,h,M,s):
        """ set reading frame to date
        """
        
        self.soc.set_par(self.unit, 5941, 6, [d,m,y,h,M,s])
        
    def inc_date(self):
        """ set reading frame to next frame
        """
        
        self.soc.set_par(self.unit, 5940, 1, [0,])
    
    def read_points(self):
        """ read data log register number points
        """
        
        # points are in pars 5975 ...
        return self.soc.get_par(self.unit, 5975, 18)
        
    def read_data(self):
        """ read current frame date and data
        
        return a tupple of current reading line (timestamp, data... )
        """
        
        # data is in pars 5951 ...
        data = self.soc.get_par(self.unit, 5951, 18)
        
        # date and time are in pars 5941 ...
        d,m,y,h,M,s = self.soc.get_par(self.unit, 5941, 6)
        time_tuple = map(int, (y,m,d,h,M,s,0,0,0))
        
        try:
            timestamp = calendar.timegm(time_tuple)
        except:
            timestamp = 0
        
        return (timestamp,) + data

    def dump_line(self, f, frame):
        """ dump data line to data-base, csv-file and stdout
        """
        
        frame_time_str_csv = time.strftime(CSV_DATETIME_FORMAT, time.gmtime(frame[0]))
        csv_line = "%s,%s" % (frame_time_str_csv, ",".join(["%.02f" % p for p in frame[1:]]))
        
        try:
            f.write("%s\n" % csv_line)
        except Exception, e:
            pass
    
    def get_point_title(self, item, points):
        """
        """
        
        point = points.filter_by(item=int(item)).first()
        
        if point:
            return point.title
            
        return "P%02d" % item
        
    def get_data(self, file_name, form, points):
        """
        """
        
        print "file", file_name
        
        try:
            f = open(path + '/' + file_name + ".part", 'w')
        except Exception, e:
            return
        
        # set unit number
        self.unit = int(form.unit.data.cpu)
        
        # try to parse the date string
        struct_time = form.date.data.timetuple()
        y,m,d,h,M,s,wd,yd,tz = struct_time
        
        # try to read trend points
        trend_points = self.read_points()
        trend_headers = [self.get_point_title(i, points) for i in trend_points]
        
        # write headers to first line
        csv_line = ",".join(["time",] + trend_headers)
        try:
            f.write("%s\n" % csv_line)
        except Exception, e:
            pass
        
        # read N frames starting from timestamp
        try:
            self.set_date(d,m,y,h,M,s)
        except Exception, e:
            pass
        
        # read data
        i = 0
        while i < (int(form.number.data)) and self.run:
            # get new data line
            try:
                frame = self.read_data()
                self.inc_date()
            except Exception, e:
                pass
            
            # if we have valid line 
            if frame[0] != 0:
                self.dump_line(f, frame)
            
            self.busy_percent = 100.0 * float(i) / float(form.number.data)
            i += 1
        
        f.close()
        self.soc.close()
        
        # rename file
        os.rename(path + '/' + file_name + ".part", path + '/' + file_name)
        
        self.busy_flag = False

