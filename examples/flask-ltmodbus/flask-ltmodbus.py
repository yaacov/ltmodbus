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
import webbrowser

from flask.ext import admin

from app import app, db, path, logger, files
from models import Points, Coms, Unit
from views import PointsView, ComsView, UnitView, HomeView

if __name__ == '__main__':
    # Create directory
    try:
        os.mkdir(path)
    except OSError:
        pass
    
    # Create admin interface
    admin = admin.Admin(app, 'Flash Trends', index_view=HomeView(name='Home'))
    
    admin.add_view(UnitView(Unit, db.session, name='Units', category='Setup'))
    admin.add_view(ComsView(Coms, db.session, name='Serial coms', category='Setup'))
    admin.add_view(PointsView(Points, db.session, category='Setup'))
    
    admin.add_view(files)

    # Open web browser
    #webbrowser.open('http://127.0.0.1:8080/admin/')

    # Start app
    app.run(debug=True, host='0.0.0.0', port=8080)

