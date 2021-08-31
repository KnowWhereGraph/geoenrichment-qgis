
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
from .kwg_geoenrichment_dialog import kwg_geoenrichmentDialog
from .kwg_property_geoenrichment_dialog import kwg_property_geoenrichmentDialog
from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_util import kwg_util as UTIL
from .kwg_json2field import kwg_json2field as Json2Field


class kwg_property_enrichment:
    count = 0
    propertyNameList = []
    propertyURLList = []
    propertyURLDict = dict()

    sosaObsPropNameList = []
    sosaObsPropURLList = []
    sosaObsPropURLDict = dict()

    inversePropertyNameList = []
    inversePropertyURLList = []
    inversePropertyURLDict = dict()


    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Linked Data Geographic Entities Property Enrichment"
        self.description = "Get the most common properties from a Knowledge Graph which supports GeoSPARQL based on the retrieved KG entities"
        self.canRunInBackground = False
        # self.propertyURLList = []
        # propertyNameList = []
        self.count += 1
        self.SPARQLQuery = kwg_sparqlquery()
        self.SPARQLUtil = UTIL()
        self.JSON2Field  = Json2Field()
        self.inplaceIRIList = []
        self.loadIRIList()
        self.sparqlEndpoint = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"
        self.path_to_gpkg = "/var/local/QGIS/kwg_results.gpkg"
        self.layerName = "geo_results"


    def getCommonProperties(self):

        # get the direct common property
        commonPropertyJSONObj = self.SPARQLQuery.commonPropertyQuery(inplaceIRIList=self.inplaceIRIList,
                                                                doSameAs=False)
        commonPropertyJSON = commonPropertyJSONObj["results"]["bindings"]


        if len(commonPropertyJSON) == 0:
            QgsMessageLog.logMessage("Couldn't find common properties", "kwg_geoenrichment", level=Qgis.Warning)

        else:

            self.propertyURLDict = self.SPARQLQuery.extractCommonPropertyJSON(commonPropertyJSON,
                                                                 p_url_list=kwg_property_enrichment.propertyURLList,
                                                                 p_name_list=kwg_property_enrichment.propertyNameList,
                                                                 url_dict=kwg_property_enrichment.propertyURLDict,
                                                                 p_var="p",
                                                                 plabel_var="pLabel",
                                                                numofsub_var="NumofSub")

        return self.propertyURLDict


    def getsosaObsPropNameList(self):

        if len(self.propertyURLDict) > 0:

            # query for common sosa observable property
            commonSosaObsPropJSONObj = self.SPARQLQuery.commonSosaObsPropertyQuery(self.inplaceIRIList,
                                                                                   doSameAs=False)

            commonSosaObsPropJSON = commonSosaObsPropJSONObj["results"]["bindings"]
            if len(commonSosaObsPropJSON) > 0:
                self.sosaObsPropURLDict = self.SPARQLQuery.extractCommonPropertyJSON(
                    commonSosaObsPropJSON,
                    p_url_list=self.sosaObsPropURLList,
                    p_name_list=self.sosaObsPropNameList,
                    url_dict=self.sosaObsPropURLDict,
                    p_var="p",
                    plabel_var="pLabel",
                    numofsub_var="NumofSub")

        return self.sosaObsPropURLDict


    def getInverseCommonProp(self):

        inverseCommonPropertyJSONObj = self.SPARQLQuery.inverseCommonPropertyQuery(self.inplaceIRIList, doSameAs=True)

        inverseCommonPropertyJSON = inverseCommonPropertyJSONObj["results"]["bindings"]

        if len(inverseCommonPropertyJSON) == 0:
            QgsMessageLog.logMessage("No inverse property found!", "kwg_geoenrichment", level=Qgis.Warning)
        else:

            self.inversePropertyURLDict = self.SPARQLQuery.extractCommonPropertyJSON(
                inverseCommonPropertyJSON,
                p_url_list=self.inversePropertyURLList,
                p_name_list=self.inversePropertyNameList,
                url_dict=self.inversePropertyURLDict,
                p_var="p",
                plabel_var="pLabel",
                numofsub_var="NumofSub")

        return

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


    def execute(self, parameters, ifaceObj=None, sparql_endpoint = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"):
        """The source code of the tool."""

        propertyList = parameters["propertySelect"]
        sparql_endpoint = parameters["sparql_endpoint"]

        # QgsMessageLog.logMessage("count: {0}".format(kwg_property_enrichment.count), "kwg_geoenrichment", level=Qgis.Info)

        selectPropertyURLList = []
        selectSosaObsPropURLList = []

        if len(propertyList) > 0:

            QgsMessageLog.logMessage("propertySplitList: {0}".format(propertyList), "kwg_geoenrichment", level=Qgis.Info)
            for propertyItem in propertyList:
                if propertyItem in self.propertyURLDict:
                    selectPropertyURLList.append(self.propertyURLDict[propertyItem])
                elif propertyItem in self.sosaObsPropURLDict:
                    selectSosaObsPropURLList.append(
                        self.sosaObsPropURLDict[propertyItem])

            # QgsMessageLog.logMessage("selectPropertyURLList: " + str(selectPropertyURLList), "kwg_geoenrichment", level=Qgis.Info)
            # QgsMessageLog.logMessage("selectSosaObsPropURLList: " + str(selectSosaObsPropURLList), "kwg_geoenrichment",
            #                          level=Qgis.Info)
            # QgsMessageLog.logMessage(selectPropertyURLList, "kwg_geoenrichment", level=Qgis.Info)

            # send a SPARQL query to DBpedia endpoint to test whether the properties are functionalProperty
            isFuncnalPropertyJSON = self.SPARQLQuery.functionalPropertyQuery(selectPropertyURLList,
                                                                             sparql_endpoint = sparql_endpoint)
            # isFuncnalPropertyJSON = isFuncnalPropertyJSONObj["results"]["bindings"]

            FunctionalPropertySet = set()
            # QgsMessageLog.logMessage("isFunctionalPropertyJSON: {0}".format(json.dumps(isFuncnalPropertyJSON)), "kwg_geoenrichment", level=Qgis.Info)

            for jsonItem in isFuncnalPropertyJSON:
                functionalPropertyURL = jsonItem["property"]["value"]
                FunctionalPropertySet.add(functionalPropertyURL)

            # get the value for each functionalProperty
            FunctionalPropertyList = list(FunctionalPropertySet)

            # QgsMessageLog.logMessage("FunctionalPropertyList: {0}".format(str(FunctionalPropertyList)), "kwg_geoenrichment", level=Qgis.Info)

            # add these functionalProperty value to feature class table
            for functionalProperty in FunctionalPropertyList:
                functionalPropertyJSON = self.SPARQLQuery.propertyValueQuery(self.inplaceIRIList, functionalProperty,
                                                                            sparql_endpoint=sparql_endpoint,
                                                                            doSameAs=False)
                # functionalPropertyJSON = functionalPropertyJSONObj["results"]["bindings"]

                # QgsMessageLog.logMessage("functionalPropertyJSON: {0}".format(json.dumps(functionalPropertyJSON)),
                #                          "kwg_geoenrichment", level=Qgis.Info)

                # # TODO: handle this adding to table
                results = self.JSON2Field.addFieldInTableByMapping(functionalPropertyJSON, "wikidataSub", "o",
                                                   "place_iri", functionalProperty, False, gpkgLocation=self.path_to_gpkg )

                if results:
                    ifaceObj.mapCanvas().refresh()
                    QgsMessageLog.logMessage("update - functional property write successful",
                                         "kwg_geoenrichment", level=Qgis.Info)


            selectPropertyURLSet = set(selectPropertyURLList)
            noFunctionalPropertySet = selectPropertyURLSet.difference(FunctionalPropertySet)
            noFunctionalPropertyList = list(noFunctionalPropertySet)

            # QgsMessageLog.logMessage("noFunctionalPropertyList: {0}".format(str(noFunctionalPropertyList)), "kwg_geoenrichment", level=Qgis.Info)

            for noFunctionalProperty in noFunctionalPropertyList:
                noFunctionalPropertyJSON = self.SPARQLQuery.propertyValueQuery(self.inplaceIRIList, noFunctionalProperty,
                                                                          sparql_endpoint=sparql_endpoint,
                                                                          doSameAs=False)

                # QgsMessageLog.logMessage("noFunctionalPropertyJSON: {0}".format(json.dumps(noFunctionalPropertyJSON)), "kwg_geoenrichment", level=Qgis.Info)

                # noFunctionalPropertyJSON = noFunctionalPropertyJSONObj["results"]["bindings"]
                # create a seperate table to store one-to-many property value, return the created table name
                success = self.JSON2Field.createMappingTableFromJSON(
                    noFunctionalPropertyJSON, "wikidataSub", "o",
                    noFunctionalProperty, "URL", False, False, outputLocation=self.path_to_gpkg, ifaceObj=ifaceObj)

                if success:
                    ifaceObj.mapCanvas().refresh()

                # TODO:  QGIS implementation for relationship class
                # creat relationship class between the original feature class and the created table
                #
                # relationshipClassName = featureClassName + "_" + tableName + "_RelClass"
                # arcpy.CreateRelationshipClass_management(featureClassName, tableName, relationshipClassName, "SIMPLE",
                #                                          noFunctionalProperty, "features from Knowledge Graph",
                #                                          "FORWARD", "ONE_TO_MANY", "NONE", "URL", "URL")

                # check whether the object of propertyURL is geo-entity
                # if it is create new feature class
                # for propertyURL in selectPropertyURLList:
                propertyURL = noFunctionalProperty
                geoCheckJSON = self.SPARQLQuery.checkGeoPropertyquery(self.inplaceIRIList, propertyURL,
                                                                 sparql_endpoint=sparql_endpoint,
                                                                 doSameAs=False)
                geometry_cnt = int(geoCheckJSON[0]["cnt"]["value"])

                QgsMessageLog.logMessage(
                    "geometry_cnt: {0}".format(str(geometry_cnt)),
                    "kwg_geoenrichment", level=Qgis.Info)

                if geometry_cnt > 0:
                    # OK, propertyURL is a property whose value is geo-entities
                    # get their geometries, create a feature layer
                    GeoQueryResult = self.SPARQLQuery.twoDegreePropertyValueWKTquery(self.inplaceIRIList, propertyURL,
                                                                                sparql_endpoint=sparql_endpoint,
                                                                                doSameAs=False)

                    # QgsMessageLog.logMessage(
                    #     "GeoQueryResult: {0}".format(json.dumps(GeoQueryResult)),
                    #     "kwg_geoenrichment", level=Qgis.Info)
                    # in_place_IRI_desc = arcpy.Describe(in_place_IRI)

                    # arcpy.AddMessage("input feature class: {}".format(in_place_IRI_desc.name))
                    # arcpy.AddMessage("input feature class: {}".format(in_place_IRI_desc.path))

                    prop_name = self.SPARQLUtil.getPropertyName(propertyURL)

                    out_geo_feature_class_name = "{}_{}".format(self.layerName, prop_name)
                    self.JSON2Field.createQGISFeatureClassFromSPARQLResult(GeoQueryResult=GeoQueryResult,
                                                                  feat_class=out_geo_feature_class_name, ifaceObj=ifaceObj)

                    # TODO: manage the geometry relationship class for QGIS
                    # out_relationshipClassName = out_geo_feature_class_name + "_" + tableName + "_RelClass"
                    # arcpy.CreateRelationshipClass_management(origin_table=out_geo_feature_class_name,
                    #                                          destination_table=tableName,
                    #                                          out_relationship_class=out_relationshipClassName,
                    #                                          relationship_type="SIMPLE",
                    #                                          forward_label="is " + noFunctionalProperty + " Of",
                    #                                          backward_label="features from Knowledge Graph",
                    #                                          message_direction="FORWARD",
                    #                                          cardinality="ONE_TO_MANY",
                    #                                          attributed="NONE",
                    #                                          origin_primary_key="URL",
                    #                                          origin_foreign_key=currentValuePropertyName)

            # sosa property value query
            for p_url in selectSosaObsPropURLList:
                sosaPropValJSON = self.SPARQLQuery.sosaObsPropertyValueQuery(self.inplaceIRIList, p_url,
                                                                        sparql_endpoint=sparql_endpoint,
                                                                        doSameAs=False)

                # QgsMessageLog.logMessage(
                #     "sosaPropValJSON: {0}".format(json.dumps(sosaPropValJSON)),
                #     "kwg_geoenrichment", level=Qgis.Info)

                success = Json2Field.createMappingTableFromJSON(sosaPropValJSON,
                                                                            keyPropertyName="wikidataSub",
                                                                            valuePropertyName="o",
                                                                            valuePropertyURL=p_url,
                                                                            keyPropertyFieldName="URL",
                                                                            isInverse=False,
                                                                            isSubDivisionTable=False,
                                                                            outputLocation=self.path_to_gpkg,
                                                                            ifaceObj=ifaceObj)

                if success:
                    ifaceObj.mapCanvas().refresh()

                # TODO: manage the sosa relationship class for QGIS
                # sosaRelationshipClassName = featureClassName + "_" + sosaTableName + "_RelClass"
                # arcpy.CreateRelationshipClass_management(featureClassName, sosaTableName,
                #                                          sosaRelationshipClassName, "SIMPLE",
                #                                          p_url, "features from Knowledge Graph",
                #                                          "FORWARD", "ONE_TO_MANY", "NONE", "URL", "URL")

        return


if __name__ == '__main__':
    kwg_property_enrichment_object = kwg_property_enrichment()
    kwg_property_enrichment_object.loadIRIList()
    pass
