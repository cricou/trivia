# -*- encoding: utf-8 -*-
############################################################################################
#
#    Copyright (C) 2020 Ambition Telecom. All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################################

{
    'name' : 'Trivia Here Map',
    'version' : '1.0',
    'author' : 'Cyril RICOU',
    'website' : '',
    'description' : """""",
    "depends" : [],
    'images': [],
    "data" : [
        "views/here_map_view.xml"
    ],
    'qweb': [
        "static/src/js/view/xml/widget.xml"
    ],
    "test": [],
    "uninstall_hook": "uninstall_hook",
    "installable" : True,
}