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

from app import db

# Create models
class Points(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(64))
    units = db.Column(db.String(16))
    item = db.Column(db.Integer)
    
    # Required for administrative interface
    def __str__(self):
        return self.title
   
class Coms(db.Model):
    com_choices=[('COM%d'%i,'COM%d'%i) for i in range(1,31)]+[('/dev/ttyUSB0', 'USB0'),('/dev/ttyUSB1', 'USB1')]
    
    id = db.Column(db.Integer, primary_key=True)
    com = db.Column(db.String(16), unique=True, nullable=False)
    baud = db.Column(db.Integer, default=4800)
    
    databits  = db.Column(db.Integer, default=8)
    parity = db.Column(db.String(16), default='E')
    stopbits = db.Column(db.Integer, default=1)
    timeout = db.Column(db.Integer, default=1)
    
    # Required for administrative interface
    def __str__(self):
        return dict(self.com_choices)[self.com]

class Unit(db.Model):
    number = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(64))
    
    com_id = db.Column(db.Integer, db.ForeignKey(Coms.id))
    com = db.relationship(Coms, backref='unit')
    cpu = db.Column(db.Integer, default=31)
    
    # Required for administrative interface
    def __str__(self):
        return self.title

