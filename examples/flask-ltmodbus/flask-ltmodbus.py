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
import webbrowser

from flask import Flask,redirect, flash
from flask import render_template
from flask import send_from_directory
from flask import request

from flask.ext.sqlalchemy import SQLAlchemy

from wtforms import Form, BooleanField, TextField, PasswordField, DateTimeField, validators
from wtforms.fields import SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from flask.ext import admin
from flask.ext.admin import form
from flask.ext.admin import Admin, BaseView, expose, AdminIndexView
from flask.ext.admin.contrib import sqla
from flask.ext.admin.contrib import fileadmin
from flask.ext.admin.form.fields import Select2Field, TimeField

from ltmodbus import LTModbusTCP, LTModbusSerial

# Create application
app = Flask(__name__, static_folder='files')

# csv format
CSV_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conf/settings.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

path = op.join(op.dirname(__file__), 'files')
busy_flag = False
busy_percent = 0

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
    com_choices=[('COM1', 'COM1'), ('COM2', 'COM2'), ('/dev/ttyUSB0', 'USB0')]
    
    id = db.Column(db.Integer, primary_key=True)
    com = db.Column(db.String(16), unique=True, nullable=False)
    baud = db.Column(db.Integer)
    
    databits  = db.Column(db.Integer)
    parity = db.Column(db.String(16))
    stopbits = db.Column(db.Integer)
    timeout = db.Column(db.Integer)
    
    # Required for administrative interface
    def __str__(self):
        return dict(self.com_choices)[self.com]

class Unit(db.Model):
    number = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(64))
    
    com_id = db.Column(db.Integer, db.ForeignKey(Coms.id))
    com = db.relationship(Coms, backref='unit')
    cpu = db.Column(db.Integer)
    
    # Required for administrative interface
    def __str__(self):
        return self.title
        
# Customized Post model admin
class PointsView(sqla.ModelView):
    # Visible columns in the list view
    column_list = ['title', 'units', 'item']
    
    column_searchable_list = ('title', Points.title)
    column_default_sort = 'item'

class UnitView(sqla.ModelView):
    com_choices=[('COM1', 'COM1'), ('COM2', 'COM2'), ('/dev/ttyUSB0', 'USB0')]
    
    # Visible columns in the list view
    column_list = ['title', 'com', 'cpu']
    
    column_searchable_list = ('title', Unit.title)
    column_default_sort = 'title'
    
class ComsView(sqla.ModelView):
    form_columns = ('com', 'baud', 'databits', 'parity', 'stopbits', 'timeout')
    
    com_choices=[('COM1', 'COM1'), ('COM2', 'COM2'), ('/dev/ttyUSB0', 'USB0')]
    parity_choices=[('E', 'Even'), ('O', 'Odd'), ('N', 'None')]
    stopbits_choices=[('0', 'No'), ('1', '1')]
    timeout_choices=[('1', '1s'), ('1.5', '1.5s')]
    
    # Visible columns in the list view
    form_overrides = dict(
        com=Select2Field,
        baud=Select2Field,
        databits=Select2Field,
        parity=Select2Field,
        stopbits=Select2Field,
        timeout=Select2Field)
    column_formatters = dict(
        com=lambda v, c, m, p: dict(v.com_choices)[m.com],
        parity=lambda v, c, m, p: dict(v.parity_choices)[m.parity],
        stopbits=lambda v, c, m, p: dict(v.stopbits_choices)[str(m.stopbits)],
        timeout=lambda v, c, m, p: dict(v.timeout_choices)[str(m.timeout)],
        )
    form_args = dict(
        # Pass the choices to the `SelectField`
        com=dict(
            choices=com_choices
        ),
        baud=dict(
            choices=[('4800', '4800'), ('19600', '19600'), ('38400', '38400')]
        ),
        databits=dict(
            choices=[('8', '8'),('7', '7')]
        ),
        parity=dict(
            choices=parity_choices
        ),
        stopbits=dict(
            choices=stopbits_choices
        ),
        timeout=dict(
            choices=timeout_choices
        ))

class RegistrationForm(Form):
    unit = QuerySelectField('Select Unit', widget = form.Select2Widget(), query_factory=lambda: Unit.query)
    date = DateTimeField('From date',widget=form.DateTimePickerWidget(),default=lambda: datetime.datetime.now() - datetime.timedelta(hours=1))
    number = Select2Field('Length', choices=[('50','50 records'),('100','100 records'),('500','500 records')])

# Flask views
@app.route('/')
def index():
    return redirect("/admin")

@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory('static/', filename)

def dump_line(f, frame):
    """ dump data line to data-base, csv-file and stdout
    """
    
    frame_time_str_csv = time.strftime(CSV_DATETIME_FORMAT, time.gmtime(frame[0]))
    csv_line = "%s,%s" % (frame_time_str_csv, ",".join(["%.02f" % p for p in frame[1:]]))
    
    try:
        f.write("%s\n" % csv_line)
    except Exception, e:
        flash("%s" % e)

def read_data(soc, file_name, form):
    """
    """
    global busy_flag
    global busy_percent
    
    try:
        f = open(path + '/' + file_name + ".part", 'w')
    except Exception, e:
        flash('%s' % e, 'error')
        return
    
    # create comunication object
    ser = LTModbusLogger(soc)
    
    # set unit number
    ser.unit = int(form.unit.data.cpu)
    
    # try to parse the date string
    struct_time = form.date.data.timetuple()
    y,m,d,h,M,s,wd,yd,tz = struct_time
    
    # read N frames starting from timestamp
    try:
        ser.set_date(d,m,y,h,M,s)
    except Exception, e:
        flash("%s" % e)
    
    # read data
    for i in range(int(form.number.data)):
        # get new data line
        try:
            frame = ser.read_data()
            ser.inc_date()
        except Exception, e:
            flash("%s" % e)
        
        # if we have valid line 
        if frame[0] != 0:
            dump_line(f, frame)
        
        busy_percent = 100.0 * float(i) / float(form.number.data)
    
    f.close()
    soc.close()
    
    # rename file
    os.rename(path + '/' + file_name + ".part", path + '/' + file_name)
    
    busy_flag = False
    
class HomeView(AdminIndexView):
    @expose("/", methods=('GET', 'POST'))
    def index(self):
        global busy_flag
        global busy_percent
        
        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            file_name = "%s_%s_%s.csv" % (form.unit.data, form.date.data.strftime("%Y-%m-%d_%H-%M"),form.number.data)
            file_name = file_name.lower().replace(' ','_')
            
            if busy_flag:
                flash('Working on earlier request, please wait... (%d%%)' % busy_percent, 'error')
                return self.render('admin/home.html', form=form)
            
            busy_flag = True
            
            soc = None
            try:
                soc = LTModbusSerial(
                    port=form.unit.data.com.com, 
                    baudrate=form.unit.data.com.baud, 
                    bytesize=form.unit.data.com.databits, 
                    parity=form.unit.data.com.parity, 
                    stopbits=1)
                soc.timeout = form.unit.data.com.timeout
            except Exception, e:
                flash('%s' % e, 'error')
            
            if soc:
                msg = 'Writing data to file "%s", please wait...' % file_name
                flash(msg)
                
                thread.start_new_thread(read_data, (soc, file_name, form))
                
        return self.render('admin/home.html', form=form)

if __name__ == '__main__':
    # Create directory
    try:
        os.mkdir(path)
    except OSError:
        pass
    
    # Create admin interface
    admin = admin.Admin(app, 'Flash Trends', index_view=HomeView(name='Home'))
    
    admin.add_view(UnitView(Unit, db.session, name='Units',  category='Setup'))
    admin.add_view(ComsView(Coms, db.session, name='Serial coms',  category='Setup'))
    admin.add_view(PointsView(Points, db.session, category='Setup'))
    
    files = fileadmin.FileAdmin(path, '/files/', name='Files')
    files.can_upload = False
    files.can_mkdir = False
    
    admin.add_view(files)

    # Open web browser
    #webbrowser.open('http://127.0.0.1:8080/admin/')

    # Start app
    app.run(debug=True, host='0.0.0.0', port=8080)

