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

from wtforms import Form, DateTimeField
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from flask.ext.admin import form
from flask.ext.admin.form.fields import Select2Field

from models import Points, Coms, Unit

class UnitReadForm(Form):
    unit = QuerySelectField(
        'Select Unit', 
        widget = form.Select2Widget(), 
        query_factory=lambda: Unit.query)
    date = DateTimeField(
        'From date',
        widget=form.DateTimePickerWidget(),
        default=lambda: datetime.datetime.now() - datetime.timedelta(hours=1))
    todate = DateTimeField(
        'To date',
        widget=form.DateTimePickerWidget(),
        default=lambda: datetime.datetime.now())
    number = Select2Field(
        'Max length', 
        choices=[('50','50 records'),('100','100 records'),('500','500 records')])

