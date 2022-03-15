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
import geojson
from PyQt5 import QtCore
from PyQt5.QtCore import QVariant
from qgis._core import QgsMessageLog, Qgis, QgsFields, QgsField, QgsVectorLayer, QgsFeature, QgsGeometry, \
    QgsVectorFileWriter, QgsProject

from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_sparqlutil import kwg_sparqlutil
from .kwg_util import kwg_util as UTIL

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'kwg_plugin_enrichment_dialog_base.ui'))


class kwg_pluginEnrichmentDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
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
        self.logger.setLevel(logging.DEBUG)  # or whatever
        handler = logging.FileHandler(
            '/var/local/QGIS/kwg_geoenrichment.log', 'w',
            'utf-8')  # or whatever
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')  # or whatever
        handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
        self.logger.addHandler(handler)
        self.params = {}
        self.spoDict = {}
        self.s2Cells = []
        self.EntityLi = []

        self.sparql_query = kwg_sparqlquery()
        self.sparql_util = kwg_sparqlutil()

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

        """
        self.setStyleSheet(stylesheet)

    def setParams(self, params):
        self.params.update(params)
        self.ifaceObj = self.params["ifaceObj"]

    def execute(self):
        # manage first degree
        self.results = {}

        # retrieve S2 cells
        s2CellBindingObject = self.sparql_query.getS2CellsFromGeometry(sparql_endpoint=self.params["end_point"],
                                                wkt_literal=self.params["wkt_literal"])

        self.logger.debug(json.dumps(s2CellBindingObject))
        for obj in s2CellBindingObject:
            self.logger.debug(json.dumps(obj))
            try:
                # self.logger.debug(obj["s2Cell"]["value"])
                self.s2Cells.append(obj["s2Cell"]["value"])
            except Exception as e:
                self.logger.debug(e)
                continue

        QgsMessageLog.logMessage("S2 Cells : " + json.dumps(self.s2Cells), "kwg_unified", level=Qgis.Info)

        # retrieve Entity associated with S2 cells
        entityBindingObject = self.sparql_query.getEntityValuesFromS2Cells(sparql_endpoint=self.params["end_point"],
                                                                           s2Cells=self.s2Cells)

        for obj in entityBindingObject:
            try:
                self.EntityLi.append(obj["entity"]["value"])
            except Exception as e:
                continue

        QgsMessageLog.logMessage("Entity List : " + json.dumps(self.EntityLi), "kwg_unified", level=Qgis.Info)

        self.populateFirstDegreeSubject()
        self.comboBox_S0.currentIndexChanged.connect(lambda: self.populateFirstDegreePredicate())
        return

    def get_results(self):
        return self.results

    def populateFirstDegreeSubject(self):
        classObject = self.sparql_query.getFirstDegreeClass(sparql_endpoint=self.params["end_point"],
                                                                           entityList=self.EntityLi)

        self.comboBox_S0.clear()
        self.comboBox_S0.addItem("--- SELECT ---")

        # populate the spoDict
        self.spoDict[0] = {}
        self.spoDict[0]["s"] = {}
        for obj in classObject:
            self.spoDict[0]["s"][obj["type"]["value"]] = self.sparql_util.make_prefixed_iri(obj["label"]["value"])

        for key in self.spoDict[0]["s"]:
            self.comboBox_S0.addItem(self.sparql_util.make_prefixed_iri(key))

    def populateFirstDegreePredicate(self):
        self.comboBox_P0.clear()
        self.comboBox_P0.addItem("--- SELECT ---")

        self.sub0 = self.comboBox_S0.currentText()
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
            self.comboBox_P0.addItem(self.sparql_util.make_prefixed_iri(key))

        self.comboBox_P0.currentIndexChanged.connect(self.populateFirstDegreeObject)
        return

    def populateFirstDegreeObject(self):
        self.pred0 = self.comboBox_P0.currentText()
        self.comboBox_O0.clear()
        self.comboBox_O0.addItem("--- SELECT ---")

        firstDegreeObject = self.sparql_query.getFirstDegreeObject(sparql_endpoint=self.params["end_point"],
                                                                    entityList=self.EntityLi,
                                                                    firstDegreeClass=self.sub0,
                                                                    firstDegreePredicate = self.pred0)

        # populate the spoDict
        self.spoDict[0]["o"] = {}
        for obj in firstDegreeObject:
            if "label" in obj:
                self.spoDict[0]["o"][obj["type"]["value"]] = self.sparql_util.make_prefixed_iri(obj["label"]["value"])
            else:
                self.spoDict[0]["o"][obj["type"]["value"]] = ""

        for key in self.spoDict[0]["o"]:
            self.comboBox_O0.addItem(self.sparql_util.make_prefixed_iri(key))
        self.comboBox_O0.currentIndexChanged.connect(self.populateSecondDegreeSubject)

    def populateSecondDegreeSubject(self):
        self.comboBox_S1.clear()
        self.comboBox_S1.addItem("--- SELECT ---")
        self.spoDict[1] = {}
        self.spoDict[1]["s"] = {}
        for key in self.spoDict[0]["o"]:
            self.comboBox_S1.addItem(self.sparql_util.make_prefixed_iri(key))
            self.spoDict[1]["s"][key] = self.spoDict[0]["o"][key]
        index = self.comboBox_O0.findText(self.comboBox_O0.currentText(), QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.comboBox_S1.setCurrentIndex(index)
        # self.populateSecondDegreePredicate()

    def populateSecondDegreePredicate(self):
        self.comboBox_P1.clear()
        self.comboBox_P1.addItem("--- SELECT ---")
        secondPropertyURLList = []
        secondPropertyURLList.extend(self.getSecondDegreeProperty())
        self.comboBox_P1.addItems(list(set(secondPropertyURLList)))
        self.comboBox_P1.currentIndexChanged.connect(self.populateSecondDegreeObject)
        return

    def populateSecondDegreeObject(self):
        self.pred1 = self.comboBox_P1.currentText()
        self.comboBox_O1.clear()
        self.comboBox_O1.addItem("--- SELECT ---")
        secondObjectList = []
        if "objectTypeList" in self.secondPredicateObjectDict[self.pred1]:
            secondObjectList.extend(self.secondPredicateObjectDict[self.pred1]["objectTypeList"])
        else:
            secondObjectList.extend(self.secondPredicateObjectDict[self.pred1]["objectList"])
        self.comboBox_O1.addItems(list(set(secondObjectList)))
        # QgsMessageLog.logMessage(str(secondObjectList), "kwg_geoenrichment", level=Qgis.Info)
        # QgsMessageLog.logMessage(self.pred1, "kwg_geoenrichment", level=Qgis.Info)
        self.comboBox_O1.currentIndexChanged.connect(self.populateThirdDegreeSubject)

    def populateThirdDegreeSubject(self):
        self.comboBox_S2.clear()
        self.comboBox_S2.addItem("--- SELECT ---")
        secondObjectList = []
        secondObjectList.extend(self.secondPredicateObjectDict[self.pred1]["objectTypeList"])
        self.comboBox_S2.addItems(list(set(secondObjectList)))
        index = self.comboBox_O1.findText(self.comboBox_O1.currentText(), QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.comboBox_S2.setCurrentIndex(index)
        self.populateThirdDegreePredicate()

    def populateThirdDegreePredicate(self):
        self.comboBox_P2.clear()
        self.comboBox_P2.addItem("--- SELECT ---")
        thirdPropertyURLList = []
        thirdPropertyURLList.extend(self.getThirdDegreeProperty())
        self.comboBox_P2.addItems(thirdPropertyURLList)
        self.comboBox_P2.currentIndexChanged.connect(self.populateThirdDegreeObject)
        return

    def populateThirdDegreeObject(self):
        self.pred2 = self.comboBox_P2.currentText()
        self.comboBox_O2.clear()
        self.comboBox_O2.addItem("--- SELECT ---")
        thirdObjectList = []
        if "objectTypeList" in self.thirdPredicateObjectDict[self.pred2]:
            if "40.2" in self.thirdPredicateObjectDict[self.pred2]:
                self.thirdPredicateObjectDict[self.pred2]["objectTypeList"].remove("40.2")
            thirdObjectList.extend(self.thirdPredicateObjectDict[self.pred2]["objectTypeList"])
        else:
            if "40.2" in self.thirdPredicateObjectDict[self.pred2]:
                self.thirdPredicateObjectDict[self.pred2]["objectList"].remove("40.2")
            thirdObjectList.extend(self.thirdPredicateObjectDict[self.pred2]["objectList"])
        self.comboBox_O2.addItems(list(set(thirdObjectList)))
        index_2 = self.comboBox_O2.findText("40.2")
        self.comboBox_O2.removeItem(index_2)
        # QgsMessageLog.logMessage(str(thirdObjectList), "kwg_geoenrichment", level=Qgis.Info)
        # QgsMessageLog.logMessage(self.pred1, "kwg_geoenrichment", level=Qgis.Info)
        # self.comboBox_O2.currentIndexChanged.connect(self.populateThirdDegreeSubject)

    def firstDegreeSubjectHandler(self):
        self.sub0 = self.comboBox_S0.currentText()
        self.results["contentType"] = self.sub0
        self.sub0_url = self.sparql_util.remake_prefixed_iri(self.sub0)

        geoSPARQLResponse = self.sparql_query.TypeAndGeoSPARQLQuery(sparql_endpoint=self.params["end_point"],
                                                                    selectedURL=self.sub0_url,
                                                                    query_geo_wkt=self.params["wkt_literal"],
                                                                    geosparql_func=self.params["geosparql_func"])

        # QgsMessageLog.logMessage("GeoJSON response received from the server", "kwg_geoenrichment",
        #                          level=Qgis.Info)
        self.handleGeoJSONObject(geoResult=geoSPARQLResponse)

        # handle predicate retrieval
        self.loadIRIList()
        self.populateFirstDegreePredicate()

    def handleGeoJSONObject(self, geoResult):
        # QgsMessageLog.logMessage("handleGeoJSONObject", "kwg_geoenrichment", level=Qgis.Info)

        with open('/var/local/QGIS/kwg_data.geojson', 'w') as f:
            geojson.dump(geoResult, f)

        geopackagedResponse = self.createGeoPackageFromSPARQLResult(geoResult)
        # self.createShapeFileFromSPARQLResult(geoResult)

        if (geopackagedResponse):
            QgsMessageLog.logMessage("Successfully created a geopackage file", "kwg_geoenrichment", level=Qgis.Info)
        else:
            QgsMessageLog.logMessage("Error while writing geopackage", "kwg_geoenrichment", level=Qgis.Error)

        pass

    def createGeoPackageFromSPARQLResult(self, GeoQueryResult, out_path="/var/local/QGIS/kwg_results.gpkg",
                                         inPlaceType="", selectedURL="",
                                         isDirectInstance=False):
        '''
        GeoQueryResult: a sparql query result json obj serialized as a list of dict()
                    SPARQL query like this:
                    select distinct ?place ?placeLabel ?placeFlatType ?wkt
                    where
                    {...}
        out_path: the output path for the create geo feature class
        inPlaceType: the label of user spercified type IRI
        selectedURL: the user spercified type IRI
        isDirectInstance: True: use placeFlatType as the type of geo-entity
                          False: use selectedURL as the type of geo-entity
        '''
        # a set of unique WKT for each found places
        placeIRISet = set()
        placeList = []
        geom_type = None

        util_obj = UTIL()

        layerFields = QgsFields()
        layerFields.append(QgsField('place_iri', QVariant.String))
        layerFields.append(QgsField('label', QVariant.String))
        layerFields.append(QgsField('type_iri', QVariant.String))

        for idx, item in enumerate(GeoQueryResult):
            wkt_literal = item["wkt"]["value"]
            # for now, make sure all geom has the same geometry type
            if idx == 0:
                geom_type = util_obj.get_geometry_type_from_wkt(wkt_literal)
            else:
                if geom_type != util_obj.get_geometry_type_from_wkt(wkt_literal):
                    # QgsMessageLog.logMessage("%s is not equal to %s"%(geom_type, util_obj.get_geometry_type_from_wkt(wkt_literal)), "kwg_geoenrichment", level=Qgis.Info)
                    pass

            if isDirectInstance == False:
                placeType = item["placeFlatType"]["value"]
            else:
                placeType = selectedURL
            print("{}\t{}\t{}".format(
                item["place"]["value"], item["placeLabel"]["value"], placeType))
            if len(placeIRISet) == 0 or item["place"]["value"] not in placeIRISet:
                placeIRISet.add(item["place"]["value"])
                placeList.append(
                    [item["place"]["value"], item["placeLabel"]["value"], placeType, wkt_literal])

        if geom_type is None:
            raise Exception("geometry type not found")

        vl = QgsVectorLayer(geom_type + "?crs=epsg:4326", "geo_results", "memory")
        pr = vl.dataProvider()
        pr.addAttributes(layerFields)
        vl.updateFields()

        if len(placeList) == 0:
            QgsMessageLog.logMessage("No {0} within the provided polygon can be finded!".format(inPlaceType),
                                     level=Qgis.Info)
        else:

            if out_path == None:
                QgsMessageLog.logMessage("No data will be added to the map document.", level=Qgis.Info)
            else:

                for item in placeList:
                    place_iri, label, type_iri, wkt_literal = item
                    wkt = wkt_literal.replace("<http://www.opengis.net/def/crs/OGC/1.3/CRS84>", "")

                    feat = QgsFeature()
                    geom = QgsGeometry.fromWkt(wkt)

                    # TODO: handle the CRS
                    # feat.setGeometry(self.transformSourceCRStoDestinationCRS(geom, src=4326, dest=3857))

                    feat.setGeometry(geom)
                    feat.setAttributes(item[0:3])

                    pr.addFeature(feat)
                vl.updateExtents()

                options = QgsVectorFileWriter.SaveVectorOptions()
                options.layerName = 'geo_results'
                context = QgsProject.instance().transformContext()
                error = QgsVectorFileWriter.writeAsVectorFormatV2(vl, out_path, context, options)
                self.ifaceObj.addVectorLayer(out_path, 'geo_results', 'ogr')

        return error[0] == QgsVectorFileWriter.NoError

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
        self.results["in_place_iri"] = self.inplaceIRIList

        return

    def getFirstDegreeProperty(self):
        # decided to work in both directions
        self.firstDirection = "BOTH"
        # get the first property URL list
        firstPropertyURLListJsonBindingObject = self.sparql_query.relFinderCommonPropertyQuery(self.inplaceIRIList,
                                                                                               relationDegree=1,
                                                                                               propertyDirectionList=[
                                                                                                   self.firstDirection],
                                                                                               selectPropertyURLList=[
                                                                                                   "",
                                                                                                   "",
                                                                                                   ""],
                                                                                               sparql_endpoint=
                                                                                               self.params["end_point"])
        self.results["firstPropertyURLListJsonBindingObject"] = firstPropertyURLListJsonBindingObject
        firstPropertyURLList = []
        firstPredicateObjectDict = {}
        for jsonItem in firstPropertyURLListJsonBindingObject:
            propertyURL = jsonItem["p1"]["value"]
            firstPropertyURLList.append(propertyURL)
            propertyPrefixedIRI = self.sparql_util.make_prefixed_iri(propertyURL)
            if propertyPrefixedIRI in firstPredicateObjectDict:
                if type(jsonItem["o1"]["value"]) is str or jsonItem["o1"]["value"].isnumeric():
                    firstPredicateObjectDict[propertyPrefixedIRI]["objectList"].append("Literal")
                else:
                    firstPredicateObjectDict[propertyPrefixedIRI]["objectList"].append(
                        self.sparql_util.make_prefixed_iri(jsonItem["o1"]["value"]))
                if "o1type" in jsonItem and jsonItem["o1type"]["value"] is not None and not jsonItem["o1type"][
                    "value"].startswith("_:node"):
                    firstPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"].append(
                        self.sparql_util.make_prefixed_iri(jsonItem["o1type"]["value"]))
            else:
                firstPredicateObjectDict[propertyPrefixedIRI] = {}
                firstPredicateObjectDict[propertyPrefixedIRI]["objectList"] = []
                firstPredicateObjectDict[propertyPrefixedIRI]["objectList"].append(
                    self.sparql_util.make_prefixed_iri(jsonItem["o1"]["value"]))
                if "o1type" in jsonItem and jsonItem["o1type"]["value"] is not None and not jsonItem["o1type"][
                    "value"].startswith("_:node"):
                    firstPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"] = []
                    firstPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"].append(
                        self.sparql_util.make_prefixed_iri(jsonItem["o1type"]["value"]))

        if self.params["end_point"] == self.sparql_util._WIKIDATA_SPARQL_ENDPOINT:
            firstPropertyLabelJSON = self.sparql_query.locationCommonPropertyLabelQuery(firstPropertyURLList,
                                                                                        sparql_endpoint=self.params[
                                                                                            "end_point"])
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
            firstPropertyLabelList = self.sparql_util.make_prefixed_iri_batch(firstPropertyURLList)

        self.firstPropertyLabelURLDict = dict(zip(firstPropertyLabelList, firstPropertyURLList))
        self.firstPredicateObjectDict = firstPredicateObjectDict

        return firstPropertyLabelList

    def getSecondDegreeProperty(self):
        self.secondDirection = "BOTH"

        # get the second property URL list
        secondPropertyURLListJsonBindingObject = self.sparql_query.relFinderCommonPropertyQuery(self.inplaceIRIList,
                                                                                                relationDegree=2,
                                                                                                propertyDirectionList=[
                                                                                                    self.firstDirection,
                                                                                                    self.secondDirection],
                                                                                                selectPropertyURLList=[
                                                                                                    self.firstPropertyLabelURLDict[
                                                                                                        self.pred0],
                                                                                                    "", ""],
                                                                                                sparql_endpoint=
                                                                                                self.params[
                                                                                                    "end_point"])
        self.results["secondPropertyURLListJsonBindingObject"] = secondPropertyURLListJsonBindingObject
        secondPropertyURLList = []
        secondPredicateObjectDict = {}

        for jsonItem in secondPropertyURLListJsonBindingObject:
            propertyURL = jsonItem["p2"]["value"]
            secondPropertyURLList.append(propertyURL)
            propertyPrefixedIRI = self.sparql_util.make_prefixed_iri(propertyURL)
            if propertyPrefixedIRI in secondPredicateObjectDict:
                if type(jsonItem["o2"]["value"]) is str or jsonItem["o2"]["value"].isnumeric():
                    secondPredicateObjectDict[propertyPrefixedIRI]["objectList"].append(
                        "Literal")
                else:
                    secondPredicateObjectDict[propertyPrefixedIRI]["objectList"].append(
                        self.sparql_util.make_prefixed_iri(jsonItem["o2"]["value"]))
                if "o2type" in jsonItem and jsonItem["o2type"]["value"] is not None and not jsonItem["o2type"][
                    "value"].startswith("_:node"):
                    secondPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"].append(
                        self.sparql_util.make_prefixed_iri(jsonItem["o2type"]["value"]))
            else:
                secondPredicateObjectDict[propertyPrefixedIRI] = {}
                secondPredicateObjectDict[propertyPrefixedIRI]["objectList"] = []
                secondPredicateObjectDict[propertyPrefixedIRI]["objectList"].append(
                    self.sparql_util.make_prefixed_iri(jsonItem["o2"]["value"]))
                if "o2type" in jsonItem and jsonItem["o2type"]["value"] is not None and not jsonItem["o2type"][
                    "value"].startswith("_:node"):
                    secondPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"] = []
                    secondPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"].append(
                        self.sparql_util.make_prefixed_iri(jsonItem["o2type"]["value"]))

        # QgsMessageLog.logMessage(json.dumps(secondPredicateObjectDict), "kwg_geoenrichment",level=Qgis.Info)

        if self.params["end_point"] == self.sparql_util._WIKIDATA_SPARQL_ENDPOINT:
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
            secondPropertyLabelList = self.sparql_util.make_prefixed_iri_batch(secondPropertyURLList)

        self.secondPropertyLabelURLDict = dict(zip(secondPropertyLabelList, secondPropertyURLList))
        self.secondPredicateObjectDict = secondPredicateObjectDict

        return list(set(secondPropertyLabelList))

    def getThirdDegreeProperty(self):

        self.thirdDirection = "BOTH"

        # get the third property URL list
        thirdPropertyURLListJsonBindingObject = self.sparql_query.relFinderCommonPropertyQuery(self.inplaceIRIList,
                                                                                               relationDegree=3,
                                                                                               propertyDirectionList=[
                                                                                                   self.firstDirection,
                                                                                                   self.secondDirection,
                                                                                                   self.thirdDirection],
                                                                                               selectPropertyURLList=[
                                                                                                   self.firstPropertyLabelURLDict[
                                                                                                       self.pred0],
                                                                                                   self.secondPropertyLabelURLDict[
                                                                                                       self.pred1],
                                                                                                   ""],
                                                                                               sparql_endpoint=
                                                                                               self.params["end_point"])
        thirdPropertyURLList = []
        thirdPredicateObjectDict = {}
        self.results["thirdPropertyURLListJsonBindingObject"] = thirdPropertyURLListJsonBindingObject
        for jsonItem in thirdPropertyURLListJsonBindingObject:
            propertyURL = jsonItem["p3"]["value"]
            thirdPropertyURLList.append(propertyURL)
            propertyPrefixedIRI = self.sparql_util.make_prefixed_iri(propertyURL)
            if propertyPrefixedIRI in thirdPredicateObjectDict:
                if type(jsonItem["o3"]["value"]) is str or jsonItem["o3"]["value"].isnumeric() or jsonItem["o3"][
                    "type"] == "literal":
                    thirdPredicateObjectDict[propertyPrefixedIRI]["objectList"].append("Literal")
                else:
                    if jsonItem["o3"]["value"] == 40.2 or jsonItem["o3"]["value"] == "40.2":
                        pass
                    else:
                        thirdPredicateObjectDict[propertyPrefixedIRI]["objectList"].append(
                            self.sparql_util.make_prefixed_iri(jsonItem["o3"]["value"]))
                if "o3type" in jsonItem and jsonItem["o3type"]["value"] is not None and not jsonItem["o3type"][
                    "value"].startswith("_:node"):
                    thirdPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"].append(
                        self.sparql_util.make_prefixed_iri(jsonItem["o3type"]["value"]))
            else:
                thirdPredicateObjectDict[propertyPrefixedIRI] = {}
                thirdPredicateObjectDict[propertyPrefixedIRI]["objectList"] = []
                thirdPredicateObjectDict[propertyPrefixedIRI]["objectList"].append(
                    self.sparql_util.make_prefixed_iri(jsonItem["o3"]["value"]))
                if "o3type" in jsonItem and jsonItem["o3type"]["value"] is not None and not jsonItem["o3type"][
                    "value"].startswith("_:node"):
                    thirdPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"] = []
                    if type(jsonItem["o3type"]["value"]) is str or jsonItem["o3type"]["value"].isnumeric() or \
                            jsonItem["o3type"][
                                "type"] == "literal":
                        thirdPredicateObjectDict[propertyPrefixedIRI]["objectList"].append("Literal")
                    else:
                        if jsonItem["o3type"]["value"] == 40.2 or jsonItem["o3type"]["value"] == "40.2":
                            pass
                        else:
                            thirdPredicateObjectDict[propertyPrefixedIRI]["objectTypeList"].append(
                                self.sparql_util.make_prefixed_iri(jsonItem["o3type"]["value"]))

        if self.params["end_point"] == self.sparql_util._WIKIDATA_SPARQL_ENDPOINT:
            thirdPropertyLabelJSON = self.sparql_query.locationCommonPropertyLabelQuery(thirdPropertyURLList,
                                                                                        sparql_endpoint=self.params[
                                                                                            "end_point"])

            # get the third property label list
            thirdPropertyURLList = []
            thirdPropertyLabelList = []
            for jsonItem in thirdPropertyLabelJSON:
                propertyURL = jsonItem["p"]["value"]
                thirdPropertyURLList.append(propertyURL)
                propertyName = jsonItem["propertyLabel"]["value"]
                thirdPropertyLabelList.append(propertyName)
        else:
            thirdPropertyLabelList = self.sparql_util.make_prefixed_iri_batch(thirdPropertyURLList)

        self.thirdPropertyLabelURLDict = dict(zip(thirdPropertyLabelList, thirdPropertyURLList))
        self.thirdPredicateObjectDict = thirdPredicateObjectDict

        return list(set(thirdPropertyLabelList))
