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

import os.path as op

from flask import Flask
from flask import redirect

from flask.ext.admin.contrib import fileadmin
from flask.ext.sqlalchemy import SQLAlchemy

from ltmodbus_logger import LTModbusLogger

# Create application
app = Flask(__name__, static_folder='files')

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conf/settings.sqlite'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

# static files path
path = op.join(op.dirname(__file__), 'files')

# serial comunication
logger = LTModbusLogger()

# admin files interface
files = fileadmin.FileAdmin(path, '/files/', name='Files')
files.can_upload = False
files.can_mkdir = False

# Flask routes
@app.route('/')
def index():
    return redirect("/admin")

@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory('static/', filename)

