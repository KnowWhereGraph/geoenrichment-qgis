# -*- coding: utf-8 -*-
"""
/***************************************************************************
 kwg_property_geoenrichmentDialog
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

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QComboBox, QLayout
from PyQt5.uic.properties import QtCore
from qgis._core import QgsMessageLog, Qgis, QgsVectorLayer

from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_sparqlutil import kwg_sparqlutil
from .kwg_util import kwg_util as UTIL
from .kwg_json2field import kwg_json2field as Json2Field

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'kwg_linkedData_relationship_finder_dialog_base.ui'))


class kwg_linkedDataDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(kwg_linkedDataDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        # self.verticalLayout.setSpacing(20)
        # self.verticalLayout.setSizeConstraint(QLayout.SetNoConstraint)
        self.setWindowTitle("KWG Linked-Data Relation Finder tool")
        self.firstPropertyLabelURLDict = dict()
        self.secondPropertyLabelURLDict = dict()
        self.thirdPropertyLabelURLDict = dict()
        self.fourthPropertyLabelURLDict = dict()
        self.firstPropertyLabel = None
        self.secondPropertyLabel = None
        self.thirdPropertyLabel = None
        self.fourthPropertyLabel = None
        self.widgets = dict()
        self.SPARQLQuery = kwg_sparqlquery()
        self.SPARQLUtil = kwg_sparqlutil()
        self.inplaceIRIList = []
        self.Util = UTIL()
        self.JSON2Field = Json2Field()
        self.sparqlEndpoint = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"
        self.path_to_gpkg = "/var/local/QGIS/kwg_results.gpkg"
        self.layerName = "geo_results"
        self.inplaceIRIList = []
        self.propertyCounter = 0
        self.counterDict = {
            1: "First",
            2: "Second",
            3: "Third",
            4: "Fourth"
        }

        self.secondDegreeInit = False
        self.thirdDegreeInit = False

        self.processRelFinder()
        # self.processLRDF()


    def processRelFinder(self):
        # load the place IRI list
        self.loadIRIList()

        # init
        self.onClick()
        self.populateFirstDegreeProperty()

        # bind the event to the button click
        self.addContent.clicked.connect(self.onClick)

        QgsMessageLog.logMessage("place URIs loaded successfully.", "kwg_geoenrichment",
                                 level=Qgis.Info)
        #
        # if int(self.degreeVal) > 2:
        #     self.comboBox_2.currentIndexChanged.connect(self.populateThirdDegreeProperty)


    def updateDegreeVal(self):
        self.degreeVal = self.comboBox_degree.currentText()


    def loadIRIList(self, path_to_gpkg='/var/local/QGIS/kwg_results.gpkg', layerName="geo_results"):
        # get the path to a geopackage e.g. /home/project/data/data.gpkg
        iriList = []

        gpkg_places_layer = path_to_gpkg + "|layername=%s" % (layerName)

        vlayer = QgsVectorLayer(gpkg_places_layer, layerName, "ogr")

        if not vlayer.isValid():
            return iriList
        else:
            for feature in vlayer.getFeatures():
                attrs = feature.attributes()
                iriList.append(attrs[1])

        self.inplaceIRIList = iriList
        # QgsMessageLog.logMessage(", ".join(iriList), "kwg_geoenrichment",
        #                          level=Qgis.Info)


        return


    def populateFirstDegreeProperty(self):
        if self.propertyCounter > 0:
            firstPropertyURLList = ["--- SELECT ---"]
            firstPropertyURLList.extend(self.getFirstDegreeProperty())
            QgsMessageLog.logMessage(",".join(firstPropertyURLList))
            # self.comboBox_1.clear()
            self.widgets["comboBox_1"].addItems(firstPropertyURLList)
            self.widgets["comboBox_1"].currentIndexChanged.connect(self.updateFirstDegreeSelection)
            return


    def getFirstDegreeProperty(self):
        # decided to work in both directions
        self.firstDirection = "BOTH"
        # get the first property URL list
        firstPropertyURLListJsonBindingObject = self.SPARQLQuery.relFinderCommonPropertyQuery(self.inplaceIRIList,
                                                                                         relationDegree=1,
                                                                                         propertyDirectionList=[
                                                                                             self.firstDirection],
                                                                                         selectPropertyURLList=["", "",
                                                                                                                ""],
                                                                                         sparql_endpoint=self.sparqlEndpoint)
        firstPropertyURLList = []
        for jsonItem in firstPropertyURLListJsonBindingObject:
            firstPropertyURLList.append(jsonItem["p1"]["value"])

        if self.sparqlEndpoint == self.SPARQLUtil._WIKIDATA_SPARQL_ENDPOINT:
            firstPropertyLabelJSON = self.SPARQLQuery.locationCommonPropertyLabelQuery(firstPropertyURLList,
                                                       sparql_endpoint=self.sparqlEndpoint)
            # firstPropertyLabelJSON = firstPropertyLabelJSONObj["results"]["bindings"]

            # get the first property label list
            firstPropertyURLList = []
            firstPropertyLabelList = []
            for jsonItem in firstPropertyLabelJSON:
                propertyURL = jsonItem["p"]["value"]
                firstPropertyURLList.append(propertyURL)
                propertyName = jsonItem["propertyLabel"]["value"]
                firstPropertyLabelList.append(propertyName)
        else:
            firstPropertyLabelList = self.SPARQLUtil.make_prefixed_iri_batch(firstPropertyURLList)

        self.firstPropertyLabelURLDict = dict(zip(firstPropertyLabelList, firstPropertyURLList))

        return list(set(firstPropertyLabelList))


    def updateFirstDegreeSelection(self):
        self.firstPropertyLabel = self.widgets["comboBox_1"].currentText()

        if self.firstPropertyLabel == None or self.firstPropertyLabel == "--- SELECT ---":
            self.firstPropertyURL = ""
            return
        else:
            self.firstPropertyURL = self.firstPropertyLabelURLDict[self.firstPropertyLabel]

        if self.propertyCounter > 1:
            try:
                self.widgets["comboBox_2"].currentIndexChanged.disconnect(self.updateFirstDegreeSelection)
            except Exception as e:
                pass
            self.widgets["comboBox_2"].clear()
            self.populateSecondDegreeProperty()
        return


    def populateSecondDegreeProperty(self):
        if self.propertyCounter > 1:
            secondPropertyURLList  = ["--- SELECT ---"]
            secondPropertyURLList.extend(self.getSecondDegreeProperty())
            # QgsMessageLog.logMessage(", ".join(secondPropertyURLList), "kwg_geoenrichment",
            #                                                   level=Qgis.Info)

            # self.comboBox_2.clear()
            self.widgets["comboBox_2"].addItems(secondPropertyURLList)
            self.widgets["comboBox_2"].currentIndexChanged.connect(self.updateSecondDegreeSelection)
            return


    def getSecondDegreeProperty(self):
        self.secondDirection = "BOTH"

        # get the second property URL list
        secondPropertyURLListJsonBindingObject = self.SPARQLQuery.relFinderCommonPropertyQuery(self.inplaceIRIList,
                                                                                          relationDegree=2,
                                                                                          propertyDirectionList=[
                                                                                              self.firstDirection,
                                                                                              self.secondDirection],
                                                                                          selectPropertyURLList=[
                                                                                              self.firstPropertyURL, "", ""],
                                                                                          sparql_endpoint=self.sparqlEndpoint)
        secondPropertyURLList = []
        for jsonItem in secondPropertyURLListJsonBindingObject:
            secondPropertyURLList.append(jsonItem["p2"]["value"])

        if self.sparqlEndpoint == self.SPARQLUtil._WIKIDATA_SPARQL_ENDPOINT:
            secondPropertyLabelJSON = self.SPARQLQuery.locationCommonPropertyLabelQuery(secondPropertyURLList,
                                                                                   sparql_endpoint=self.sparqlEndpoint)
            # secondPropertyLabelJSON = secondPropertyLabelJSONObj["results"]["bindings"]

            # get the second property label list
            secondPropertyURLList = []
            secondPropertyLabelList = []
            for jsonItem in secondPropertyLabelJSON:
                propertyURL = jsonItem["p"]["value"]
                secondPropertyURLList.append(propertyURL)
                propertyName = jsonItem["propertyLabel"]["value"]
                secondPropertyLabelList.append(propertyName)
        else:
            secondPropertyLabelList = self.SPARQLUtil.make_prefixed_iri_batch(secondPropertyURLList)

        self.secondPropertyLabelURLDict = dict(zip(secondPropertyLabelList, secondPropertyURLList))

        return list(set(secondPropertyLabelList))


    def updateSecondDegreeSelection(self):
        self.secondPropertyLabel = self.widgets["comboBox_2"].currentText()

        if self.secondPropertyLabel == None or self.secondPropertyLabel == "--- SELECT ---":
            self.secondPropertyURL = ""
            return
        else:
            self.secondPropertyURL = self.secondPropertyLabelURLDict[self.secondPropertyLabel]

        if self.propertyCounter > 2:
            try:
                self.widgets["comboBox_3"].currentIndexChanged.disconnect(self.updateFirstDegreeSelection)
            except Exception as e:
                pass
            self.widgets["comboBox_3"].clear()
            self.populateThirdDegreeProperty()


    def populateThirdDegreeProperty(self):
        if self.propertyCounter > 2:
            thirdPropertyURLList = ["--- SELECT ---"]
            thirdPropertyURLList.extend(self.getThirdDegreeProperty())
            # QgsMessageLog.logMessage(", ".join(secondPropertyURLList), "kwg_geoenrichment",
            #                                                   level=Qgis.Info)

            # self.comboBox_3.clear()
            self.widgets["comboBox_3"].addItems(thirdPropertyURLList)
            self.widgets["comboBox_3"].currentIndexChanged.connect(self.updateThirdDegreeSelection)
            return


    def getThirdDegreeProperty(self):

        self.thirdDirection = "BOTH"

        # get the third property URL list
        thirdPropertyURLListJsonBindingObject = self.SPARQLQuery.relFinderCommonPropertyQuery(self.inplaceIRIList,
                                                                                         relationDegree=3,
                                                                                         propertyDirectionList=[
                                                                                             self.firstDirection,
                                                                                             self.secondDirection,
                                                                                             self.thirdDirection],
                                                                                         selectPropertyURLList=[
                                                                                             self.firstPropertyURL,
                                                                                             self.secondPropertyURL, ""],
                                                                                         sparql_endpoint=self.sparqlEndpoint)
        thirdPropertyURLList = []
        for jsonItem in thirdPropertyURLListJsonBindingObject:
            thirdPropertyURLList.append(jsonItem["p3"]["value"])

        if self.sparqlEndpoint == self.SPARQLUtil._WIKIDATA_SPARQL_ENDPOINT:
            thirdPropertyLabelJSON = self.SPARQLQuery.locationCommonPropertyLabelQuery(thirdPropertyURLList,
                                                                                  sparql_endpoint=self.sparqlEndpoint)

            # get the third property label list
            thirdPropertyURLList = []
            thirdPropertyLabelList = []
            for jsonItem in thirdPropertyLabelJSON:
                propertyURL = jsonItem["p"]["value"]
                thirdPropertyURLList.append(propertyURL)
                propertyName = jsonItem["propertyLabel"]["value"]
                thirdPropertyLabelList.append(propertyName)
        else:
            thirdPropertyLabelList = self.SPARQLUtil.make_prefixed_iri_batch(thirdPropertyURLList)

        self.thirdPropertyLabelURLDict = dict(zip(thirdPropertyLabelList, thirdPropertyURLList))

        return list(set(thirdPropertyLabelList))


    def updateThirdDegreeSelection(self):
        self.thirdPropertyLabel = self.widgets["comboBox_3"].currentText()

        if self.thirdPropertyLabel == None or self.thirdPropertyLabel == "--- SELECT ---":
            self.thirdPropertyURL = ""
            return
        else:
            self.thirdPropertyURL = self.thirdPropertyLabelURLDict[self.thirdPropertyLabel]
        return


    def getPropertyLabelURLDict(self):
        return self.firstPropertyLabelURLDict, self.secondPropertyLabelURLDict, self.thirdPropertyLabelURLDict, self.fourthPropertyLabelURLDict


    def getDegreeVal(self):
        return self.propertyCounter


    def onClick(self):
        self.propertyCounter += 1
        if self.propertyCounter == 1:
            labelString = "Keep exploring content"
        else:
            labelString = "More Content"

        labelObj = QLabel()
        labelObj.setText(labelString)
        labelObj.setObjectName("labelObj_{}".format(str(self.propertyCounter)))
        self.verticalLayout.addWidget(labelObj)
        self.widgets["labelObj_{}".format(str(self.propertyCounter))] = labelObj

        comboBox = QComboBox()
        comboBox.setAccessibleName("comboBox_{}".format(str(self.propertyCounter)))
        QgsMessageLog.logMessage("comboBox_{}".format(str(self.propertyCounter)), "kwg_groenrichment", level=Qgis.Info)
        comboBox.setFixedWidth(500)
        comboBox.setInsertPolicy(6)
        self.verticalLayout.addWidget(comboBox)
        self.widgets["comboBox_{}".format(str(self.propertyCounter))] = comboBox
        self.handlePropertyAdd()


        if self.propertyCounter == 4:
            self.addContent.setEnabled(False)


    def handlePropertyAdd(self):

        if self.propertyCounter == 2 and self.firstPropertyLabel is not None:
            self.populateSecondDegreeProperty()

        if self.propertyCounter == 3 and self.secondPropertyLabel is not None:
            self.populateThirdDegreeProperty()

        pass