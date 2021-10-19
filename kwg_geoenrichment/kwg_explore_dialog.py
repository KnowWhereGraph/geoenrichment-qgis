# -*- coding: utf-8 -*-
"""
/***************************************************************************
 kwg_geoenrichmentDialog
                                 A QGIS plugin
 KWG Geoenrichment plugin
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
    os.path.dirname(__file__), 'kwg_explore_dialog_base.ui'))


class kwg_exploreDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, eventPlaceTypeDict, commonPropertyNameList, commonPropertyURLList, sosaPropertyNameList, \
                sosaPropertyURLList, inversePropertyNameList, inversePropertyURLList, parent=None):
        """Constructor."""
        super(kwg_exploreDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.eventPlaceTypeDict = eventPlaceTypeDict

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

        # KWG module objects
        self.sparqlQuery = kwg_sparqlquery()

        # setting up properties
        self.commonPropertyNameList = commonPropertyNameList
        self.commonPropertyURLList = commonPropertyURLList

        self.sosaPropertyNameList = sosaPropertyNameList
        self.sosaPropertyURLList = sosaPropertyURLList

        self.inversePropertyNameList = inversePropertyNameList
        self.inversePropertyURLList = inversePropertyURLList

        # populate feature types
        self.populateEventPlaceTypes()

        # populate the table
        self.updateTableView()

        # icon
        self.toolButton.setIcon(QIcon(':/plugins/kwg_geoenrichment/resources/icon_DrawPtXY.png'))
        self.toolButton_1.setIcon(QIcon(':/plugins/kwg_geoenrichment/resources/icon_DrawL.png'))
        self.toolButton_2.setIcon(QIcon(':/plugins/kwg_geoenrichment/resources/icon_DrawP.png'))


    def populateEventPlaceTypes(self):
        for key in self.eventPlaceTypeDict:
            self.comboBox.addItem(key)
        return


    def updateTableView(self):

        propertyNameLi =  self.commonPropertyNameList.copy()
        propertyNameLi.extend(self.sosaPropertyNameList)
        propertyNameLi.extend(self.inversePropertyNameList)

        propertyURLLi = self.commonPropertyURLList.copy()
        propertyURLLi.extend(self.sosaPropertyURLList)
        propertyURLLi.extend(self.inversePropertyURLList)

        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(len(propertyNameLi))
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        tableHeader = ['Property', 'Merge Rule', "URI"]
        self.tableWidget.setHorizontalHeaderLabels(tableHeader)


        for i in range(len(propertyNameLi)):
            chkBoxItem = QTableWidgetItem(propertyNameLi[i])
            chkBoxItem.setText(propertyNameLi[i])
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)

            self.tableWidget.setItem(i, 0, chkBoxItem)

            comboBox = QComboBox()
            for txt in ["", "SUM", "MIN", "MAX", "STD-DEV", "MEAN", "COUNT", "CONCATENATE", "FIRST", "LAST"]:
                comboBox.addItem(txt)
            self.tableWidget.setCellWidget(i, 1, comboBox)

            self.tableWidget.setItem(i, 2, QTableWidgetItem(propertyURLLi[i]))

        return


    def setPropertyLists(self, commonPropertyNameList, commonPropertyURLList, sosaPropertyNameList, \
        sosaPropertyURLList, inversePropertyNameList, inversePropertyURLList):
        # re-setting up properties
        self.commonPropertyNameList = commonPropertyNameList
        self.commonPropertyURLList = commonPropertyURLList

        self.sosaPropertyNameList = sosaPropertyNameList
        self.sosaPropertyURLList = sosaPropertyURLList

        self.inversePropertyNameList = inversePropertyNameList
        self.inversePropertyURLList = inversePropertyURLList

        # populate the table
        self.updateTableView()
