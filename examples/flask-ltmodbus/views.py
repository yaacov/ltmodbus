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

from flask import request
from flask import flash
from flask.ext.admin import form
from flask.ext.admin import expose, AdminIndexView
from flask.ext.admin.contrib import sqla
from flask.ext.admin.form.fields import Select2Field, TimeField

from app import app, db, path, logger
from models import Points, Coms, Unit
from forms import UnitReadForm

# Customized Post model admin
class PointsView(sqla.ModelView):
    # Visible columns in the list view
    column_list = ['title', 'units', 'item']
    
    column_searchable_list = ('title', Points.title)
    column_default_sort = 'item'

class UnitView(sqla.ModelView):
    
    # Visible columns in the list view
    column_list = ['title', 'com', 'cpu']
    
    column_searchable_list = ('title', Unit.title)
    column_default_sort = 'title'
    
class ComsView(sqla.ModelView):
    form_columns = ('com', 'baud', 'databits', 'parity', 'timeout')
    column_list = ('com', 'baud', 'databits', 'parity', 'timeout')
    
    com_choices=[('COM%d'%i,'COM%d'%i) for i in range(1,31)]+[('/dev/ttyUSB0', 'USB0'),('/dev/ttyUSB1', 'USB1')]
    parity_choices=[('E', 'Even (default)'), ('O', 'Odd'), ('N', 'None')]
    databits_choices=[('7', '7'), ('8', '8 (default)'),]
    stopbits_choices=[('1', '1 (default)'), ('0', 'No')]
    timeout_choices=[('0.5', '0.5s'), ('1', '1.0s'), ('1.5', '1.5s'), ('3', '3.0s')]
    baud_choices=[
                ('600','600'), 
                ('1200','1200'), 
                ('2400','2400'), 
                ('4800','4800 (default)'), 
                ('9600','9600'), 
                ('19200','19.2k'), 
                ('38400','38.4k'), 
                ('115200','115.2k')]
    
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
        baud=lambda v, c, m, p: dict(v.baud_choices)[str(m.baud)],
        parity=lambda v, c, m, p: dict(v.parity_choices)[m.parity],
        databits=lambda v, c, m, p: dict(v.databits_choices)[str(m.databits)],
        stopbits=lambda v, c, m, p: dict(v.stopbits_choices)[str(m.stopbits)],
        timeout=lambda v, c, m, p: dict(v.timeout_choices)[str(m.timeout)],
        )
    form_args = dict(
        # Pass the choices to the `SelectField`
        com=dict(
            choices=com_choices
        ),
        baud=dict(
            choices=baud_choices
        ),
        databits=dict(
            choices=databits_choices
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

class HomeView(AdminIndexView):
    @expose("/", methods=('GET', 'POST'))
    def index(self):
        global logger
        
        form = UnitReadForm(request.form)
        
        if logger.busy_flag:
            flash('Working on earlier request, please wait... (%d%%)' % logger.busy_percent, 'error')
            return self.render('admin/home.html', form=form, return_url = '/admin/')
            
        if request.method == 'POST' and form.validate():
            file_name = "%s_%s_%s.csv" % (
                form.unit.data, 
                form.date.data.strftime("%Y-%m-%d_%H-%M"),
                form.number.data)
            file_name = file_name.lower().replace(' ','_')
            
            logger.busy_flag = True
            
            try:
                logger.open_soc(form.unit.data.com)
            except Exception, e:
                flash('%s' % e, 'error')
            
            if logger.soc:
                msg = 'Writing data to file "%s", please wait...' % file_name
                flash(msg)
                
                thread.start_new_thread(logger.get_data, (file_name, form))
                
                return self.render('admin/home.html', form=form, return_url = '/admin/')
                
        return self.render('admin/home.html', form=form)

