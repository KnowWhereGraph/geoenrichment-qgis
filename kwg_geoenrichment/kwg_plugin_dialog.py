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
import logging
import os
from qgis.PyQt import QtWidgets, Qt
from qgis.PyQt import uic

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSplitter, QTextEdit, QFrame, QDockWidget, QListWidget, QMessageBox

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

        # displaying help
        self.displayingHelp = False
        self.setFixedWidth(650)
        self.plainTextEdit.setHidden(True)

        # logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # or whatever
        self.path = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(self.path + "/logs"):
            os.makedirs(self.path + "/logs")
        handler = logging.FileHandler(
            self.path + '/logs/kwg_geoenrichment.log', 'w+',
            'utf-8')  # or whatever
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')  # or whatever
        handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
        self.logger.addHandler(handler)

        image_path = self.path + "/resources/background-landing.png"

        help_icon = self.path + "/resources/help-circle.png"
        self.toolButton.setIcon(QIcon(help_icon))

        self.toolButton.clicked.connect(self.displayHelp)

        bg_img = """
        QDialog {
            background-image: url("%s");
        }
        """ % (image_path)

        sshFile = self.path + "/style.qss"
        with open(sshFile, "r") as fh:
            qss = fh.read()
            qss += bg_img
            self.setStyleSheet(qss)

    def displayHelp(self):
        if self.displayingHelp:
            self.displayingHelp = False
            self.plainTextEdit.setHidden(True)
            self.setFixedWidth(650)
        else:
            self.displayingHelp = True
            self.plainTextEdit.setVisible(True)
            self.setFixedWidth(850)