
from qgis.PyQt.QtCore import QTranslator, QSettings, QCoreApplication, qVersion, QVariant
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QMenu, QInputDialog
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsFeature, QgsProject, QgsGeometry, \
    QgsCoordinateTransform, QgsCoordinateTransformContext, QgsMapLayer, \
    QgsFeatureRequest, QgsVectorLayer, QgsLayerTreeGroup, QgsRenderContext, \
    QgsCoordinateReferenceSystem, QgsWkbTypes, QgsMessageLog, Qgis, QgsFields, QgsField, QgsVectorFileWriter

import json
import re
import os

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .kwg_linkedData_relationship_finder_dialog import kwg_linkedDataDialog
from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_sparqlutil import kwg_sparqlutil
from .kwg_util import kwg_util as UTIL
from .kwg_json2field import kwg_json2field as Json2Field


class kwg_linkedData_relationship_finder:
    def __init__(self, a,b,c,d):
        """Define the tool (tool name is the name of the class)."""
        self.firstPropertyLabelURLDict = a
        self.secondPropertyLabelURLDict = b
        self.thirdPropertyLabelURLDict = c
        self.fourthPropertyLabelURLDict = d
        self.label = "Linked Data Relationship Finder"
        self.description = """Getting a table of S-P-O triples for the relationships from locations features."""
        self.canRunInBackground = False
        self.SPARQLQuery = kwg_sparqlquery()
        self.SPARQLUtil = kwg_sparqlutil()
        self.inplaceIRIList = []
        self.Util = UTIL()
        self.JSON2Field = Json2Field()
        self.sparqlEndpoint = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"
        self.path_to_gpkg = "/var/local/QGIS/kwg_results.gpkg"
        self.layerName = "geo_results"


    def execute(self, parameters, ifaceObj):
        """The source code of the tool."""
        in_sparql_endpoint = parameters["sparql_endpoint"]

        in_relation_degree = parameters["degree_val"]
        in_first_property_dir = parameters["first_degree_property_direction"]
        in_first_property = parameters["first_degree_property"]
        in_second_property_dir = parameters["second_degree_property_direction"]
        in_second_property = parameters["second_degree_property"]
        in_third_property_dir = parameters["third_degree_property_direction"]
        in_third_property = parameters["third_degree_property"]

        sparql_endpoint = in_sparql_endpoint

        # set this
        relationDegree = int(in_relation_degree)

        self.loadIRIList()

        inplaceIRIList = self.inplaceIRIList

        # get the user specified property URL and direction at each degree
        propertyDirectionList = []
        selectPropertyURLList = ["", "", ""]

        if in_first_property_dir and relationDegree >= 1:
            firstDirection = in_first_property_dir
            firstProperty = in_first_property
            if firstProperty == None:
                firstPropertyURL = ""
            else:
                firstPropertyURL = self.firstPropertyLabelURLDict[firstProperty]

            propertyDirectionList.append(firstDirection)
            selectPropertyURLList[0] = firstPropertyURL
            self.firstPropertyURL = firstPropertyURL

        if in_second_property_dir and relationDegree >= 2:
            secondDirection = in_second_property_dir
            secondProperty = in_second_property
            if secondProperty == None:
                secondPropertyURL = ""
            else:
                secondPropertyURL = self.secondPropertyLabelURLDict[secondProperty]

            propertyDirectionList.append(secondDirection)
            selectPropertyURLList[1] = secondPropertyURL
            self.secondPropertyURL = secondPropertyURL

        if in_third_property_dir and relationDegree >= 3:
            thirdDirection = in_third_property_dir
            thirdProperty = in_third_property
            if thirdProperty == None:
                thirdPropertyURL = ""
            else:
                thirdPropertyURL = self.thirdPropertyLabelURLDict[thirdProperty]

            propertyDirectionList.append(thirdDirection)
            selectPropertyURLList[2] = thirdPropertyURL
            self.thirdPropertyURL = thirdPropertyURL

        QgsMessageLog.logMessage("propertyDirectionList: {0}".format(propertyDirectionList), "kwg_geoenrichment",
                                                          level=Qgis.Info)

        QgsMessageLog.logMessage("selectPropertyURLList: {0}".format(selectPropertyURLList), "kwg_geoenrichment",
                                 level=Qgis.Info)

        # for the direction list, change "BOTH" to "ORIGIN" and "DESTINATION"
        directionExpendedLists = self.Util.directionListFromBoth2OD(propertyDirectionList)

        tripleStore = dict()
        for currentDirectionList in directionExpendedLists:
            # get a list of triples for current specified property path
            newTripleStore = self.SPARQLQuery.relFinderTripleQuery(inplaceIRIList,
                                                              propertyDirectionList=currentDirectionList,
                                                              selectPropertyURLList=selectPropertyURLList,
                                                              sparql_endpoint=sparql_endpoint)

            tripleStore = self.Util.mergeTripleStoreDicts(tripleStore, newTripleStore)

        triplePropertyURLList = []
        for triple in tripleStore:
            if triple.p not in triplePropertyURLList:
                triplePropertyURLList.append(triple.p)

        if sparql_endpoint == self.SPARQLUtil._WIKIDATA_SPARQL_ENDPOINT:

            triplePropertyLabelJSON = self.SPARQLQuery.locationCommonPropertyLabelQuery(triplePropertyURLList,
                                                                                   sparql_endpoint=self.sparqlEndpoint)

            triplePropertyURLList = []
            triplePropertyLabelList = []
            for jsonItem in triplePropertyLabelJSON:
                propertyURL = jsonItem["p"]["value"]
                triplePropertyURLList.append(propertyURL)
                propertyName = jsonItem["propertyLabel"]["value"]
                triplePropertyLabelList.append(propertyName)
        else:
            triplePropertyLabelList = self.SPARQLUtil.make_prefixed_iri_batch(triplePropertyURLList)

        triplePropertyURLLabelDict = dict(zip(triplePropertyURLList, triplePropertyLabelList))

        self.createTripleStoreTable(tripleStore, triplePropertyURLLabelDict, outputLocation=self.path_to_gpkg, ifaceObj=ifaceObj)

        entitySet = set()
        for triple in tripleStore:
            entitySet.add(triple.s)
            entitySet.add(triple.o)

        # QgsMessageLog.logMessage("entitySet: {}".format(entitySet), "kwg_geoenrichment", level=Qgis.Info)


        placeJSON = self.SPARQLQuery.endPlaceInformationQuery(list(entitySet), sparql_endpoint=self.sparqlEndpoint)
        # QgsMessageLog.logMessage("placeJSON: {}".format(placeJSON), "kwg_geoenrichment", level=Qgis.Info);


        self.createPlaceGeometryLayer(GeoQueryResult=placeJSON, isDirectInstance=False, ifaceObj=ifaceObj)

        return


    def createTripleStoreTable(self, tripleStore, triplePropertyURLLabelDict, outputLocation="", ifaceObj=None):
        tableName = "rel_finder" + "_" + "table"

        layerFields = QgsFields()
        layerFields.append(QgsField("Subject", QVariant.String))
        layerFields.append(QgsField("Predicate", QVariant.String))
        layerFields.append(QgsField("Object", QVariant.String))
        layerFields.append(QgsField("Pred_Label", QVariant.String))
        layerFields.append(QgsField("Degree", QVariant.Int))

        vl = QgsVectorLayer("POLYGON" + "?crs=epsg:4326", tableName, "memory")
        pr = vl.dataProvider()
        pr.addAttributes(layerFields)
        vl.updateFields()

        if outputLocation == None:
            QgsMessageLog.logMessage("No data will be added to the map document.", level=Qgis.Warning)
        else:

            for triple in tripleStore:
                feat = QgsFeature()

                feat.setAttributes([triple.s, triple.p, triple.o, triplePropertyURLLabelDict[triple.p], tripleStore[triple]])
                pr.addFeature(feat)
            vl.updateExtents()

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.layerName = tableName
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            context = QgsProject.instance().transformContext()
            error = QgsVectorFileWriter.writeAsVectorFormatV2(vl, outputLocation, context, options)
            ifaceObj.addVectorLayer(outputLocation, tableName, 'ogr')

        return error[0] == QgsVectorFileWriter.NoError


    def createPlaceGeometryLayer(self, GeoQueryResult, out_path="/var/local/QGIS/kwg_results.gpkg",
                                         inPlaceType="", selectedURL="",
                                         isDirectInstance=False,
                                         ifaceObj=None):
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
                assert geom_type == util_obj.get_geometry_type_from_wkt(wkt_literal)

            # if isDirectInstance == False:
            #     placeType = item["placeFlatType"]["value"]
            # else:
            placeType = selectedURL
            print("{}\t{}\t{}".format(
                item["place"]["value"], item["placeLabel"]["value"], placeType))
            if len(placeIRISet) == 0 or item["place"]["value"] not in placeIRISet:
                placeIRISet.add(item["place"]["value"])
                placeList.append(
                    [item["place"]["value"], item["placeLabel"]["value"], placeType, wkt_literal])

        if geom_type is None:
            raise Exception("geometry type not find")

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
                options.layerName = 'rel_finder_geometry'
                context = QgsProject.instance().transformContext()
                error = QgsVectorFileWriter.writeAsVectorFormatV2(vl, out_path, context, options)
                ifaceObj.addVectorLayer(out_path, 'rel_finder_geometry', 'ogr')

        return error[0] == QgsVectorFileWriter.NoError


    def loadIRIList(self, path_to_gpkg ='/var/local/QGIS/kwg_results.gpkg', layerName="geo_results"):
        # get the path to a geopackage e.g. /home/project/data/data.gpkg
        iriList = []

        gpkg_places_layer = path_to_gpkg + "|layername=%s"%(layerName)

        vlayer = QgsVectorLayer(gpkg_places_layer, layerName, "ogr")

        if not vlayer.isValid():
            return iriList
        else:
            for feature in vlayer.getFeatures():
                attrs = feature.attributes()
                iriList.append(attrs[1])

        self.inplaceIRIList = iriList

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

        return thirdPropertyLabelList


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

        return secondPropertyLabelList


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

        return firstPropertyLabelList


if __name__ == '__main__':

    pass
