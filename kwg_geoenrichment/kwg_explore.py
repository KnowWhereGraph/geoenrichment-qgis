
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
import geojson

from .resources import *
# Import the code for the dialog

from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_util import kwg_util as UTIL
from .kwg_json2field import kwg_json2field as Json2Field


class kwg_explore:

    def __init__(self, ifaceObj = None):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Linked Data Geographic Entities Property Enrichment"
        self.description = "Get the most common properties from a Knowledge Graph which supports GeoSPARQL based on the retrieved KG entities"

        self.ifaceObj = ifaceObj

        self.sparqlQuery = kwg_sparqlquery()
        self.SPARQLUtil = UTIL()
        self.JSON2Field  = Json2Field()

        self.sparqlEndpoint = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"
        self.path_to_gpkg = "/var/local/QGIS/kwg_results.gpkg"
        self.layerName = "geo_results"

        self.eventPlaceTypeDict = dict()

        # retrieving properties
        self.commonPropertyNameList = []
        self.commonPropertyURLList = []
        self.commonPropertyURLDict = dict()

        self.sosaPropertyNameList = []
        self.sosaPropertyURLList = []
        self.sosaPropertyURLDict = dict()

        self.inversePropertyNameList = []
        self.inversePropertyURLList = []
        self.inversePropertyURLDict = dict()


    def getEventPlaceTypes(self):
        # QgsMessageLog.logMessage("sending query", "kwg_explore_geoenrichment",
        #                          level=Qgis.Info)

        sparqlResultJSON = self.sparqlQuery.EventTypeSPARQLQuery()

        # QgsMessageLog.logMessage(json.dumps(sparqlResultJSON), "kwg_explore_geoenrichment",
        #                          level=Qgis.Info)

        for obj in sparqlResultJSON:
            if((obj["entityType"] is not None and obj["entityType"]["type"] is not None and obj["entityType"]["type"] == "uri" ) and
                    (obj["entityTypeLabel"] is not None and obj["entityTypeLabel"]["type"] is not None and obj["entityTypeLabel"]["type"] == "literal" )):
                self.eventPlaceTypeDict[obj["entityTypeLabel"]["value"]] = obj["entityType"]["value"]

        return self.eventPlaceTypeDict


    def retrievePropertyList(self):
        commonPropJSON = self.sparqlQuery.commonPropertyExploreQuery(sparql_endpoint=self.sparqlEndpoint)
        self.extractPropertyJSON(commonPropJSON, self.commonPropertyURLDict, self.commonPropertyURLList, self.commonPropertyNameList,"common" )

        sosaPropJSON = self.sparqlQuery.commonSosaObsPropertyExploreQuery(sparql_endpoint=self.sparqlEndpoint)
        self.extractPropertyJSON(sosaPropJSON, self.sosaPropertyURLDict, self.sosaPropertyURLList, self.sosaPropertyNameList, "sosa")

        inversePropJSON = self.sparqlQuery.inverseCommonPropertyExploreQuery(sparql_endpoint=self.sparqlEndpoint)
        self.extractPropertyJSON(inversePropJSON, self.inversePropertyURLDict, self.inversePropertyURLList, self.inversePropertyNameList, "inverse")
        pass


    def populatePropertyDict(self, propertyJSON, propertyDict, propertyList, propertyType):
        resultsBindings = propertyJSON["results"]["bindings"]
        if len(resultsBindings) > 0:
            for obj in resultsBindings:
                if "plabel" in obj:
                    propertyDict[obj["p"]["value"]] = obj["plabel"]["value"]
                else:
                    propertyDict[obj["p"]["value"]] = obj["p"]["value"]
                propertyList.append(obj["p"]["value"])

        self.logger.info(propertyType + "_li: " + str(propertyList))
        self.logger.info(propertyType + "_dict: " + json.dumps(propertyDict))


    def extractPropertyJSON(self, propertyJSON, propertyDict, propertyURLList, propertyNameList, propertyType):
        if propertyType == "inverse":
            p_var = "inverse_p"
        else:
            p_var = "p"
        resultsBindings = propertyJSON["results"]["bindings"]
        propertyDict = self.sparqlQuery.extractCommonPropertyJSON(
            resultsBindings,
            p_url_list=propertyURLList,
            p_name_list=propertyNameList,
            url_dict=propertyDict,
            p_var=p_var,
            plabel_var="plabel",
            numofsub_var=None)
        return


    def getPropertyLists(self):
        self.retrievePropertyList()
        return self.commonPropertyNameList, self.commonPropertyURLList, self.sosaPropertyNameList, \
                self.sosaPropertyURLList, self.inversePropertyNameList, self.inversePropertyURLList


    def exectue(self, exploreParams):

        self.exploreParams = exploreParams

        # update the location params:
        if self.exploreParams["output_location"] is not None: self.path_to_gpkg = self.exploreParams["output_location"]
        if self.exploreParams["feature_class"] is not None: self.layerName = self.exploreParams["feature_class"]

        self.updateExploreParams()
        self.decideFunctionalOrNonFunctional()

        self.retrievePlaceIRI()

        self.performPropertyEnrichment()

        # QgsMessageLog.logMessage("exploreP: {0}".format(json.dumps(self.exploreParams)), "kwg_geoenrichment",
        #                          level=Qgis.Info)
        return


    def decideFunctionalOrNonFunctional(self):
        self.selectedPropertyURL = []
        for prop in self.exploreParams["selectedProp"]:
            self.selectedPropertyURL.append(self.exploreParams["selectedProp"][prop]["property_uri"])
        self.exploreParams["selectedPropURL"] = self.selectedPropertyURL

        jsonBindingObjFunctionalProp = self.sparqlQuery.functionalPropertyQuery(self.selectedPropertyURL, sparql_endpoint=self.sparqlEndpoint)

        self.exploreParams["functionalPropertyList"] = []
        for obj in jsonBindingObjFunctionalProp:
            self.exploreParams["functionalPropertyList"].append(obj["property"]["value"])

        self.exploreParams["nonFunctionalPropertyList"] = [item for item in self.selectedPropertyURL if item not in self.exploreParams["functionalPropertyList"]]

        return


    def updateExploreParams(self):
        # get the function
        geosparql_func = list()
        if self.exploreParams["spatial_rel"] == "Contains or Intersects":
            geosparql_func = ["geo:sfContains", "geo:sfIntersects"]
        elif self.exploreParams["spatial_rel"] == "Contains":
            geosparql_func = ["geo:sfContains"]
        elif self.exploreParams["spatial_rel"] == "Within":
            geosparql_func = ["geo:sfWithin"]
        elif self.exploreParams["spatial_rel"] == "Intersect":
            geosparql_func = ["geo:sfIntersects"]
        else:
            QgsMessageLog.logMessage("The spatial relation is not supported!", "kwg_geoenrichment", level=Qgis.Critical)

        self.exploreParams["geosparql_func"] = geosparql_func

        self.exploreParams["feature_type"] = self.eventPlaceTypeDict[self.exploreParams["feature"]]
        return


    def retrievePlaceIRI(self):
        geoSPARQLResponse = self.sparqlQuery.TypeAndGeoSPARQLQuery(query_geo_wkt=self.exploreParams["wkt"], selectedURL=self.exploreParams["feature_type"],
                              geosparql_func=self.exploreParams["geosparql_func"])

        # self.logger.debug(json.dumps(geoSPARQLResponse))
        # QgsMessageLog.logMessage("GeoJSON response received from the server", "kwg_geoenrichment",
        #                          level=Qgis.Info)

        geopackagedResponse = self.createGeoPackageFromSPARQLResult(geoSPARQLResponse, className=self.layerName, out_path=self.path_to_gpkg)
        # self.createShapeFileFromSPARQLResult(geoResult)

        if (geopackagedResponse):
            QgsMessageLog.logMessage("Successfully created a geopackage file", "kwg_geoenrichment", level=Qgis.Info)
        else:
            QgsMessageLog.logMessage("Error while writing geopackage", "kwg_geoenrichment", level=Qgis.Error)
        return


    def createGeoPackageFromSPARQLResult(self, GeoQueryResult, className="geo_results_default", out_path="/var/local/QGIS/kwg_results.gpkg", inPlaceType="", selectedURL="",
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
                assert geom_type == util_obj.get_geometry_type_from_wkt(wkt_literal)

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
            raise Exception("geometry type not find")

        vl = QgsVectorLayer(geom_type+"?crs=epsg:4326", className, "memory")
        pr = vl.dataProvider()
        pr.addAttributes(layerFields)
        vl.updateFields()

        if len(placeList) == 0:
            QgsMessageLog.logMessage("No {0} within the provided polygon can be found!".format(inPlaceType), level=Qgis.Info)
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
                options.layerName = className
                context = QgsProject.instance().transformContext()
                error = QgsVectorFileWriter.writeAsVectorFormatV2(vl, out_path, context, options)
                self.ifaceObj.addVectorLayer(out_path, className, 'ogr')

        return error[0] == QgsVectorFileWriter.NoError


    def performPropertyEnrichment(self):
        self.loadIRIList(path_to_gpkg=self.path_to_gpkg, layerName=self.layerName)
        self.performFunctionalPropertyEnrichment()

        pass


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

        # QgsMessageLog.logMessage("inplaceIRI: {0}".format(json.dumps(self.inplaceIRIList)),
        #                          "kwg_geoenrichment", level=Qgis.Info)

        return



    def performFunctionalPropertyEnrichment(self):
        # add these functionalProperty value to feature class table

        # QgsMessageLog.logMessage("explroeParams: {0}".format(json.dumps(self.exploreParams, indent=2)),
        #                          "kwg_geoenrichment", level=Qgis.Info)

        for functionalProperty in self.exploreParams["functionalPropertyList"]:
            functionalPropertyJSON = self.sparqlQuery.propertyValueQuery(self.inplaceIRIList, functionalProperty,
                                                                         sparql_endpoint=self.sparqlEndpoint,
                                                                         doSameAs=False)

            # QgsMessageLog.logMessage("functionalPropertyJSON: {0}".format(json.dumps(functionalPropertyJSON)),
            #                          "kwg_geoenrichment", level=Qgis.Info)

            # # TODO: handle this adding to table
            results = self.JSON2Field.addFieldInTableByMapping(functionalPropertyJSON, "wikidataSub", "o",
                                                               "place_iri", functionalProperty, False,
                                                               gpkgLocation=self.path_to_gpkg, featureClassName=self.layerName)

            if results:
                self.ifaceObj.mapCanvas().refresh()
                QgsMessageLog.logMessage("update - functional property write successful",
                                         "kwg_geoenrichment", level=Qgis.Info)
        pass


    def perfromNonFunctionalPropertyEnrichment(self):
        pass



if __name__ == '__main__':
    kwg_explore_object = kwg_explore()
    kwg_explore_object.loadIRIList()
    pass
