# -*- coding: utf-8 -*-
"""
/***************************************************************************
 kwg_pluginEnrichmentDialog
                                 A QGIS plugin
 KWG plugin Enrichment
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
from qgis.PyQt import QtWidgets
from qgis.PyQt import uic

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
from PyQt5 import QtCore
from PyQt5.QtCore import QVariant, QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QComboBox, QHeaderView, QMessageBox, QCheckBox
from qgis._core import QgsMessageLog, Qgis, QgsFields, QgsField, QgsVectorLayer, QgsFeature, QgsGeometry, \
    QgsVectorFileWriter, QgsProject

from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_sparqlutil import kwg_sparqlutil
from .kwg_util import kwg_util as UTIL

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'kwg_plugin_enrichment_dialog_base.ui'))


class kwg_pluginEnrichmentDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, s2Cells=[], entityLi=[], spoDict={}, params={}):
        """Constructor."""
        super(kwg_pluginEnrichmentDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # logging
        self.logger = logging.getLogger()
        self.labelPropDict = dict()
        self.labelPropDict["LITERAL"] = "LITERAL"
        self.path = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

        if not os.path.exists(os.path.join(self.path, 'logs')):
            os.makedirs(os.path.join(self.path, 'logs'))
        handler = logging.FileHandler(os.path.join(self.path, 'logs', 'kwg_geoenrichment.log'), 'w+', 'utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
        handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
        self.logger.addHandler(handler)

        self.params = {}
        self.spoDict = spoDict
        self.s2Cells = s2Cells
        self.EntityLi = entityLi
        self.params=params
        if bool(params):
            self.ifaceObj = self.params["ifaceObj"]

        self.threadpool = QThreadPool()

        self.degreeCount = 0
        self.setUpTable()
        self.pushButton_learnMore.clicked.connect(self.addLearnMore)

        # displaying help
        self.displayingHelp = False
        self.setFixedWidth(620)
        self.plainTextEdit.setHidden(True)

        self.toolButton.setIcon(QIcon(":/plugins/kwg_geoenrichment/resources/help-circle.png"))

        self.movie = QMovie(":/plugins/kwg_geoenrichment/resources/loading.gif")
        self.loadingLabel.setMovie(self.movie)
        self.movie.start()
        self.loadingLabel.setScaledContents(True)
        self.loadingLabel.resize(27, 27)

        self.chosenVal = {}
        self.chosenVal["s"] = {}
        self.chosenVal["p"] = {}
        self.chosenVal["o"] = {}

        self.entitiesRetrieved = QCheckBox()
        self.entitiesRetrieved.setChecked(False)
        self.entitiesRetrieved.stateChanged.connect(lambda: self.populateFirstDegreeSubject())

        self.retrievingQuery = QCheckBox()
        self.retrievingQuery.setChecked(False)
        self.retrievingQuery.stateChanged.connect(lambda: self.queryStateHandler())


        self.toolButton.clicked.connect(self.displayHelp)

        self.sparql_query = kwg_sparqlquery()
        self.sparql_util = kwg_sparqlutil()

        if bool(self.spoDict):
            self.populateFirstDegreeSubject(spo=self.spoDict)

        stylesheet = os.path.join(self.path, 'style.qss')
        self.setStyleSheet(open(stylesheet, "r").read())

    def setParams(self, params):
        self.params.update(params)
        self.ifaceObj = self.params["ifaceObj"]

    def queryStateHandler(self):
        worker = Worker(self.retrievingQuery, self.fetchingLabel, self.loadingLabel)
        self.threadpool.start(worker)

    def setUpTable(self):
        self.tableWidget.setColumnCount(3)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tableWidget.horizontalHeader().hide()

        self.addLearnMore()

    def addLearnMore(self):

        # populate N degree subject based on the object property above
        if self.degreeCount > 0:
            finalObject = self.tableWidget.cellWidget(self.degreeCount - 1, 2).currentText()
            # QgsMessageLog.logMessage(str(finalObject), "kwg_geoenrichment", Qgis.Info)

            if finalObject is not None and finalObject != "--- SELECT ---" and finalObject != "LITERAL":
                self.tableWidget.insertRow(self.degreeCount)

                comboBox_S = QComboBox()
                comboBox_P = QComboBox()
                comboBox_O = QComboBox()

                self.tableWidget.setCellWidget(self.degreeCount, 0, comboBox_S)
                self.tableWidget.setCellWidget(self.degreeCount, 1, comboBox_P)
                self.tableWidget.setCellWidget(self.degreeCount, 2, comboBox_O)

                comboBox_S.show()
                comboBox_P.show()
                comboBox_O.show()

                self.tableWidget.cellWidget(self.degreeCount, 0).clear()
                self.tableWidget.cellWidget(self.degreeCount, 0).addItem("--- SELECT ---")
                self.spoDict[self.degreeCount] = {}
                self.spoDict[self.degreeCount]["s"] = {}
                for key in self.spoDict[self.degreeCount - 1]["o"]:
                    self.tableWidget.cellWidget(self.degreeCount, 0).addItem(self.updateLabelPropDict(self.sparql_util.make_prefixed_iri(key)))
                    self.spoDict[self.degreeCount]["s"][key] = self.spoDict[self.degreeCount - 1]["o"][key]
                index = self.tableWidget.cellWidget(self.degreeCount - 1, 2).findText(finalObject, QtCore.Qt.MatchFixedString)

                if index >= 0:
                    self.tableWidget.cellWidget(self.degreeCount, 0).setCurrentIndex(index)
                self.populateNDegreePredicate()
                self.degreeCount += 1
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)

                msg.setText("Can't add more content...")
                msg.setInformativeText("'LITERAL' data encountered!")
                msg.setWindowTitle("Learn More Warning!")
                msg.exec_()
        else:
            self.tableWidget.insertRow(self.degreeCount)

            comboBox_S = QComboBox()
            comboBox_P = QComboBox()
            comboBox_O = QComboBox()

            self.tableWidget.setCellWidget(self.degreeCount, 0, comboBox_S)
            self.tableWidget.setCellWidget(self.degreeCount, 1, comboBox_P)
            self.tableWidget.setCellWidget(self.degreeCount, 2, comboBox_O)

            comboBox_S.show()
            comboBox_P.show()
            comboBox_O.show()

            self.tableWidget.cellWidget(self.degreeCount, 0).clear()

            self.degreeCount += 1

    def execute(self):
        # manage first degree
        self.results = {}
        self.retrievingQuery.setChecked(True)

        # self.tableWidget.cellWidget(0, 0).clear()
        # self.tableWidget.cellWidget(0, 0).addItem("--- SELECT ---")
        s2CellBindingObject = []

        for wkt in self.params["wkt_literal"]:
            # retrieve S2 cells
            response = self.sparql_query.getS2CellsFromGeometry(sparql_endpoint=self.params["end_point"],
                                                                           wkt_literal=wkt)

            if response == "error: s2c":
                self.handleError(errCode="s2c")
                return "s2c"
            s2CellBindingObject.extend(response)

        self.logger.debug(json.dumps(s2CellBindingObject))
        for obj in s2CellBindingObject:
            self.logger.debug(json.dumps(obj))
            try:
                # self.logger.debug(obj["s2Cell"]["value"])
                self.s2Cells.append(obj["s2Cell"]["value"])
            except Exception as e:
                self.logger.debug(e)
                continue

        # retrieve Entity associated with S2 cells
        entityBindingObject = self.sparql_query.getEntityValuesFromS2Cells(sparql_endpoint=self.params["end_point"],
                                                                           s2Cells=self.s2Cells)

        for obj in entityBindingObject:
            try:
                self.EntityLi.append(obj["entity"]["value"])
            except Exception as e:
                continue

        self.entitiesRetrieved.setChecked(True)
        self.retrievingQuery.setChecked(False)
        return

    def get_results(self):
        return self.results

    def get_s2Cells(self):
        return self.s2Cells

    def get_entityLi(self):
        return self.EntityLi

    def get_spoDict(self):
        spo = {}
        spo[0] = {}
        spo[0]["s"] = self.spoDict[0]["s"]
        return spo

    def populateFirstDegreeSubject(self, spo={}):
        self.entitiesRetrieved.stateChanged.disconnect()
        self.retrievingQuery.setChecked(True)
        self.tableWidget.cellWidget(0, 0).clear()
        self.tableWidget.cellWidget(0, 0).addItem("--- SELECT ---")

        if not bool(spo):
            classObject = self.sparql_query.getFirstDegreeClass(sparql_endpoint=self.params["end_point"],
                                                                entityList=self.EntityLi)

            # populate the spoDict`
            self.spoDict[0] = {}
            self.spoDict[0]["s"] = {}
            for obj in classObject:
                self.spoDict[0]["s"][obj["type"]["value"]] = self.sparql_util.make_prefixed_iri(obj["label"]["value"])
        else:
            self.spoDict[0] = spo[0]

        for key in self.spoDict[0]["s"]:
            self.tableWidget.cellWidget(0, 0).addItem(self.updateLabelPropDict(self.sparql_util.make_prefixed_iri(key)))
        self.retrievingQuery.setChecked(False)
        self.tableWidget.cellWidget(0, 0).currentIndexChanged.connect(lambda: self.populateFirstDegreePredicate())


    def handleError(self, errCode = ""):
        QgsMessageLog.logMessage("error occured " + errCode, "kwg_geoernichment", Qgis.Info)

    def populateFirstDegreePredicate(self):
        self.tableWidget.cellWidget(0, 1).clear()
        self.tableWidget.cellWidget(0, 1).addItem("--- SELECT ---")
        self.retrievingQuery.setChecked(True)

        self.sub0 = self.labelPropDict[self.tableWidget.cellWidget(0, 0).currentText()]
        self.chosenVal["s"][0] = self.sub0
        predicateObject = self.sparql_query.getFirstDegreePredicate(sparql_endpoint=self.params["end_point"],
                                                                    entityList=self.EntityLi,
                                                                    firstDegreeClass=self.sub0)

        # populate the spoDict
        self.spoDict[0]["p"] = {}
        for obj in predicateObject:
            if "label" in obj:
                self.spoDict[0]["p"][obj["p"]["value"]] = self.sparql_util.make_prefixed_iri(obj["label"]["value"])
            else:
                self.spoDict[0]["p"][obj["p"]["value"]] = ""

        for key in self.spoDict[0]["p"]:
            self.tableWidget.cellWidget(0, 1).addItem(self.updateLabelPropDict(self.sparql_util.make_prefixed_iri(key)))

        self.retrievingQuery.setChecked(False)
        self.tableWidget.cellWidget(0, 1).currentIndexChanged.connect(self.populateFirstDegreeObject)
        return

    def populateFirstDegreeObject(self):
        self.pred0 = self.labelPropDict[self.tableWidget.cellWidget(0, 1).currentText()]
        self.chosenVal["p"][0] = self.pred0
        self.tableWidget.cellWidget(0, 2).clear()
        self.tableWidget.cellWidget(0, 2).addItem("--- SELECT ---")
        self.retrievingQuery.setChecked(True)

        firstDegreeObject = self.sparql_query.getFirstDegreeObject(sparql_endpoint=self.params["end_point"],
                                                                   entityList=self.EntityLi,
                                                                   firstDegreeClass=self.sub0,
                                                                   firstDegreePredicate=self.pred0)

        self.logger.info("firstDegreeObject : ")
        self.logger.info(json.dumps(firstDegreeObject))

        # populate the spoDict
        self.spoDict[0]["o"] = {}
        for obj in firstDegreeObject:
            if "label" in obj:
                self.spoDict[0]["o"][obj["type"]["value"]] = self.sparql_util.make_prefixed_iri(obj["label"]["value"])
            else:
                self.spoDict[0]["o"][obj["type"]["value"]] = ""

        for key in self.spoDict[0]["o"]:
            self.tableWidget.cellWidget(0, 2).addItem(self.updateLabelPropDict(self.sparql_util.make_prefixed_iri(key)))

        self.retrievingQuery.setChecked(False)
        if not self.spoDict[0]["o"]:
            self.tableWidget.cellWidget(0, 2).addItem("LITERAL")

    def populateNDegreePredicate(self):
        i = self.degreeCount
        self.tableWidget.cellWidget(i, 1).clear()
        self.tableWidget.cellWidget(i, 1).addItem("--- SELECT ---")
        selectedVal = []
        for it in range(i+1):
            selectedVal.append(self.labelPropDict[self.tableWidget.cellWidget(it, 0).currentText()])
            if it < i:
                selectedVal.append(self.labelPropDict[self.tableWidget.cellWidget(it, 1).currentText()])
        # secondPropertyURLList.extend(self.getSecondDegreeProperty())
        secondPredObj = self.sparql_query.getNDegreePredicate(sparql_endpoint=self.params["end_point"],
                                                              entityList=self.EntityLi,
                                                              selectedVals=selectedVal,
                                                              degree=i + 1)

        # populate the spoDict
        self.spoDict[i]["p"] = {}
        for obj in secondPredObj:
            if "label" in obj:
                self.spoDict[i]["p"][obj["p"]["value"]] = self.sparql_util.make_prefixed_iri(obj["label"]["value"])
            else:
                self.spoDict[i]["p"][obj["p"]["value"]] = ""

        for key in self.spoDict[i]["p"]:
            self.tableWidget.cellWidget(i, 1).addItem(self.updateLabelPropDict(self.sparql_util.make_prefixed_iri(key)))
        self.tableWidget.cellWidget(i, 1).currentIndexChanged.connect(self.populateNDegreeObject)
        return

    def populateNDegreeObject(self):
        i = self.degreeCount
        self.tableWidget.cellWidget(i - 1, 2).clear()
        self.tableWidget.cellWidget(i - 1, 2).addItem("--- SELECT ---")

        selectedVal = []
        for it in range(i):
            selectedVal.append(self.labelPropDict[self.tableWidget.cellWidget(it, 0).currentText()])
            selectedVal.append(self.labelPropDict[self.tableWidget.cellWidget(it, 1).currentText()])
        # secondPropertyURLList.extend(self.getSecondDegreeProperty())
        secondPropObj = self.sparql_query.getNDegreeObject(sparql_endpoint=self.params["end_point"],
                                                           entityList=self.EntityLi,
                                                           selectedVals=selectedVal,
                                                           degree=i)

        # populate the spoDict
        self.spoDict[i - 1]["o"] = {}
        for obj in secondPropObj:
            if "label" in obj:
                self.spoDict[i - 1]["o"][obj["type"]["value"]] = self.sparql_util.make_prefixed_iri(obj["label"]["value"])
            else:
                self.spoDict[i - 1]["o"][obj["type"]["value"]] = ""

        for key in self.spoDict[i - 1]["o"]:
            self.tableWidget.cellWidget(i - 1, 2).addItem(self.updateLabelPropDict(self.sparql_util.make_prefixed_iri(key)))

        if not self.spoDict[i - 1]["o"]:
            self.tableWidget.cellWidget(i - 1, 2).addItem("LITERAL")

    def getDegree(self):
        return self.degreeCount

    def getResults(self):

        i = self.degreeCount
        selectedVal = []
        for it in range(i):
            subject = self.labelPropDict[self.tableWidget.cellWidget(it, 0).currentText()]
            predicate = self.labelPropDict[self.tableWidget.cellWidget(it, 1).currentText()]
            if subject is not None and subject != "--- SELECT ---" and subject != "LITERAL":
                selectedVal.append(subject)
            if predicate is not None and predicate != "--- SELECT ---" and predicate != "LITERAL":
                selectedVal.append(predicate)

        finalObject = self.labelPropDict[self.tableWidget.cellWidget(i-1, 2).currentText()]
        if finalObject is not None and finalObject != "--- SELECT ---" and finalObject != "LITERAL":
            selectedVal.append(finalObject)

        self.logger.debug("selectedVal + " + str(selectedVal))

        thirdPropObj = self.sparql_query.getNDegreeResults(sparql_endpoint=self.params["end_point"],
                                                           entityList=self.EntityLi,
                                                           selectedVals=selectedVal,
                                                           degree=i)

        self.logger.debug(str(len(thirdPropObj)))
        return thirdPropObj

    def displayHelp(self):
        if self.displayingHelp:
            self.displayingHelp = False
            self.plainTextEdit.setHidden(True)
            self.setFixedWidth(620)
        else:
            self.displayingHelp = True
            self.plainTextEdit.setVisible(True)
            self.setFixedWidth(900)


    def updateLabelPropDict(self, label):
        newLabel = ""
        if ":" in label:
            newLabel = (label.split(":")[1]).strip()
        else:
            newLabel = label
        self.labelPropDict[newLabel] = label
        return newLabel


class Worker(QRunnable, ):

    def __init__(self, retrievingQuery, fetchingLabel, loadingLabel):
        super(Worker, self).__init__()
        self.retrievingQuery = retrievingQuery
        self.loadingLabel = loadingLabel
        self.fetchingLabel = fetchingLabel

    @pyqtSlot()
    def run(self):
        '''
        Runnable code for executing S2 cells query
        '''
        if (self.retrievingQuery.isChecked()):
            # QgsMessageLog.logMessage("fetching...", "kwg_geoenrichment", Qgis.Info)
            self.fetchingLabel.show()
            self.loadingLabel.show()
        else:
            # QgsMessageLog.logMessage("done!", "kwg_geoenrichment", Qgis.Info)
            self.fetchingLabel.hide()
            self.loadingLabel.hide()