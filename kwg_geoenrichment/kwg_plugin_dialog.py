# -*- coding: utf-8 -*-
"""
/***************************************************************************
 kwg_pluginDialog
                                 A QGIS plugin
 KWG  plugin
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-06-04
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Rushiraj Nenuji, University of California Santa Barbara
        email                : nenuji@nceas.ucsb.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import json
import logging
import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QComboBox
from qgis._core import QgsMessageLog, Qgis

from PyQt5.QtGui import QIcon

from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_sparqlutil import kwg_sparqlutil

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'kwg_plugin_dialog_base.ui'))


class kwg_pluginDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(kwg_pluginDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # or whatever
        handler = logging.FileHandler(
            '/var/local/QGIS/kwg_geoenrichment.log', 'w',
            'utf-8')  # or whatever
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')  # or whatever
        handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
        self.logger.addHandler(handler)

        stylesheet = """
        QWidget {
            background-image: url("/Users/nenuji/Documents/Github/kwg-qgis-geoenrichment/kwg_geoenrichment/resources/background-landing.png"); 
            opacity: 1.0;
        }
        
        QPushButton{
                background-color: #216FB3;
                color: #ffffff;
                height: 70px;
                width: 255px;
            }
            
        QComboBox{
                background-color: #216FB3;
                color: #ffffff;
                height: 70px;
            }
            
        QListWidget{
                background-color: #216FB3;
                color: #ffffff;
                height: 70px;
            }
        QLineEdit {
                height: 70px;
                width: 255px;
                background: linear-gradient(308.55deg, rgba(0,2,31,0) 0%, #00011F 100%), linear-gradient(359.14deg, rgba(0,2,31,0) 0%, #00011F 100%);
        }
        """
        self.setStyleSheet(stylesheet)

