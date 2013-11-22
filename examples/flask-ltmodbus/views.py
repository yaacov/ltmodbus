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

import datetime
import thread

from wtforms import Form, DateTimeField, validators
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from flask import request
from flask import flash
from flask.ext.admin import form
from flask.ext.admin import expose, AdminIndexView
from flask.ext.admin.contrib import sqla
from flask.ext.admin.form.fields import Select2Field, TimeField

from app import app, db, path, logger
from models import Points, Coms, Unit

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

class UnitReadForm(Form):
    unit = QuerySelectField(
        'Select Unit', 
        widget = form.Select2Widget(), 
        query_factory=lambda: Unit.query)
    date = DateTimeField(
        'From date',
        widget=form.DateTimePickerWidget(),
        default=lambda: datetime.datetime.now() - datetime.timedelta(hours=1))
    number = Select2Field(
        'Length', 
        choices=[('50','50 records'),('100','100 records'),('500','500 records')])

class HomeView(AdminIndexView):
    @expose("/", methods=('GET', 'POST'))
    def index(self):
        global logger
        
        form = UnitReadForm(request.form)
        if request.method == 'POST' and form.validate():
            file_name = "%s_%s_%s.csv" % (
                form.unit.data, 
                form.date.data.strftime("%Y-%m-%d_%H-%M"),
                form.number.data)
            file_name = file_name.lower().replace(' ','_')
            
            if logger.busy_flag:
                flash('Working on earlier request, please wait... (%d%%)' % logger.busy_percent, 'error')
                return self.render('admin/home.html', form=form)
            
            logger.busy_flag = True
            
            try:
                logger.open_soc(form.unit.data.com)
            except Exception, e:
                flash('%s' % e, 'error')
            
            if logger.soc:
                msg = 'Writing data to file "%s", please wait...' % file_name
                flash(msg)
                
                thread.start_new_thread(logger.get_data, (file_name, form))
                
        return self.render('admin/home.html', form=form)
