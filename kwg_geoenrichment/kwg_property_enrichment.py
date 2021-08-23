
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
from .kwg_json2field import kwf_json2field as Json2Field


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
        kwg_property_enrichment.count += 1
        self.SPARQLQuery = kwg_sparqlquery()
        self.inplaceIRIList = []
        self.loadIRIList()


    def getCommonProperties(self):

        # get the direct common property
        commonPropertyJSONObj = self.SPARQLQuery.commonPropertyQuery(inplaceIRIList=self.inplaceIRIList,
                                                                doSameAs=False)
        commonPropertyJSON = commonPropertyJSONObj["results"]["bindings"]

        UTIL_obj = UTIL()
        if len(commonPropertyJSON) == 0:
            QgsMessageLog.logMessage("Couldn't find common properties", "kwg_geoenrichment", level=Qgis.Warning)

        else:

            self.propertyURLDict = UTIL_obj.extractCommonPropertyJSON(commonPropertyJSON,
                                                                                             p_url_list=kwg_property_enrichment.propertyURLList,
                                                                                             p_name_list=kwg_property_enrichment.propertyNameList,
                                                                                             url_dict=kwg_property_enrichment.propertyURLDict,
                                                                                             p_var="p",
                                                                                             plabel_var="pLabel",
                                                                                             numofsub_var="NumofSub")

        return


    def getsosaObsPropNameList(self):

        if len(self.propertyURLDict) > 0:

            # query for common sosa observable property
            commonSosaObsPropJSONObj = self.SPARQLQuery.commonSosaObsPropertyQuery(self.inplaceIRIList,
                                                                                   doSameAs=False)

            commonSosaObsPropJSON = commonSosaObsPropJSONObj["results"]["bindings"]
            if len(commonSosaObsPropJSON) > 0:
                self.sosaObsPropURLDict = UTIL.extractCommonPropertyJSON(
                    commonSosaObsPropJSON,
                    p_url_list=self.sosaObsPropURLList,
                    p_name_list=self.sosaObsPropNameList,
                    url_dict=self.sosaObsPropURLDict,
                    p_var="p",
                    plabel_var="pLabel",
                    numofsub_var="NumofSub")

        return


    def getInverseCommonProp(self):

        inverseCommonPropertyJSONObj = self.SPARQLQuery.inverseCommonPropertyQuery(self.inplaceIRIList, doSameAs=True)

        inverseCommonPropertyJSON = inverseCommonPropertyJSONObj["results"]["bindings"]

        if len(inverseCommonPropertyJSON) == 0:
            QgsMessageLog.logMessage("No inverse property found!", "kwg_geoenrichment", level=Qgis.Warning)
        else:

            self.inversePropertyURLDict = UTIL.extractCommonPropertyJSON(
                inverseCommonPropertyJSON,
                p_url_list=self.inversePropertyURLList,
                p_name_list=self.inversePropertyNameList,
                url_dict=self.inversePropertyURLDict,
                p_var="p",
                plabel_var="pLabel",
                numofsub_var="NumofSub")

        return


    def loadIRIList(self):
        # get the path to a geopackage e.g. /home/project/data/data.gpkg
        path_to_gpkg ='/var/local/QGIS/kwg_results.gpkg'
        iriList = []

        gpkg_places_layer = path_to_gpkg + "|layername=kwg_results"

        vlayer = QgsVectorLayer(gpkg_places_layer, "kwg_results", "ogr")

        if not vlayer.isValid():
            return iriList
        else:
            for feature in vlayer.getFeatures():
                attrs = feature.attributes()
                iriList.append(attrs[1])

        # QgsMessageLog.logMessage(" | ".join(iriList), "kwg_geoenrichment", level=Qgis.Info)

        self.inplaceIRIList = iriList

        return


    def execute(self, parameters, messages, sparql_endpoint = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"):
        """The source code of the tool."""
        in_sparql_endpoint = sparql_endpoint
        in_place_IRI = self.loadIRIList()
        in_com_property = parameters[0]

        QgsMessageLog.logMessage(" , ".join(in_place_IRI), "kwg_geoenrichment", level=Qgis.Info)

        QgsMessageLog.logMessage("count: {0}".format(kwg_property_enrichment.count), "kwg_geoenrichment", level=Qgis.Info)

        propertySelect = in_com_property.valueAsText
        selectPropertyURLList = []
        selectSosaObsPropURLList = []

        # setting up the params
        # get all the IRI from input point feature class of wikidata places
        inplaceIRIList = []
        inputFeatureClassName = in_place_IRI.valueAsText
        featureClassName = "kwg_results"
        sparql_endpoint = in_sparql_endpoint
        in_place_IRI_desc = in_place_IRI

        if propertySelect != None:
            propertySplitList = re.split("[;]", propertySelect.replace("'", ""))
            QgsMessageLog.logMessage("propertySplitList: {0}".format(propertySplitList), "kwg_geoenrichment", level=Qgis.Info)
            for propertyItem in propertySplitList:
                if propertyItem in kwg_property_enrichment.propertyURLDict:
                    selectPropertyURLList.append(kwg_property_enrichment.propertyURLDict[propertyItem])
                elif propertyItem in kwg_property_enrichment.sosaObsPropURLDict:
                    selectSosaObsPropURLList.append(
                        kwg_property_enrichment.sosaObsPropURLDict[propertyItem])

            # send a SPARQL query to DBpedia endpoint to test whether the properties are functionalProperty
            isFuncnalPropertyJSON = self.SPARQLQuery.functionalPropertyQuery(selectPropertyURLList,
                                                                        sparql_endpoint=in_sparql_endpoint)
            # isFuncnalPropertyJSON = isFuncnalPropertyJSONObj["results"]["bindings"]

            FunctionalPropertySet = set()

            for jsonItem in isFuncnalPropertyJSON:
                functionalPropertyURL = jsonItem["property"]["value"]
                FunctionalPropertySet.add(functionalPropertyURL)

            QgsMessageLog.logMessage("FunctionalPropertySet: {0}".format(FunctionalPropertySet))

            selectPropertyURLSet = set(selectPropertyURLList)
            noFunctionalPropertySet = selectPropertyURLSet.difference(FunctionalPropertySet)
            noFunctionalPropertyList = list(noFunctionalPropertySet)

            for noFunctionalProperty in noFunctionalPropertyList:
                noFunctionalPropertyJSON = self.SPARQLQuery.propertyValueQuery(inplaceIRIList, noFunctionalProperty,
                                                                          sparql_endpoint=sparql_endpoint,
                                                                          doSameAs=False)
                # noFunctionalPropertyJSON = noFunctionalPropertyJSONObj["results"]["bindings"]
                # create a seperate table to store one-to-many property value, return the created table name
                tableName, keyPropertyFieldName, currentValuePropertyName = Json2Field.createMappingTableFromJSON(
                    noFunctionalPropertyJSON, "wikidataSub", "o",
                    noFunctionalProperty, inputFeatureClassName, "URL", False, False)
                # creat relationship class between the original feature class and the created table

                relationshipClassName = featureClassName + "_" + tableName + "_RelClass"

                # check whether the object of propertyURL is geo-entity
                # if it is create new feature class
                # for propertyURL in selectPropertyURLList:
                propertyURL = noFunctionalProperty
                geoCheckJSON = self.SPARQLQuery.checkGeoPropertyquery(inplaceIRIList, propertyURL,
                                                                 sparql_endpoint=in_sparql_endpoint,
                                                                 doSameAs=False)
                geometry_cnt = int(geoCheckJSON[0]["cnt"]["value"])
                if geometry_cnt > 0:
                    # OK, propertyURL is a property whose value is geo-entities
                    # get their geometries, create a feature layer
                    GeoQueryResult = self.SPARQLQuery.twoDegreePropertyValueWKTquery(inplaceIRIList, propertyURL,
                                                                                sparql_endpoint=sparql_endpoint,
                                                                                doSameAs=False)

                    # in_place_IRI_desc = arcpy.Describe(in_place_IRI)


                    prop_name = UTIL.getPropertyName(propertyURL)

                    out_geo_feature_class_name = "{}_{}".format(featureClassName, prop_name)
                    out_geo_feature_class_path = os.path.join(in_place_IRI_desc.path, out_geo_feature_class_name)
                    Json2Field.createFeatureClassFromSPARQLResult(GeoQueryResult=GeoQueryResult,
                                                                  out_path=out_geo_feature_class_path)

        return


if __name__ == '__main__':
    kwg_property_enrichment_object = kwg_property_enrichment()
    kwg_property_enrichment_object.loadIRIList()
    pass