
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

from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_util import kwg_util as UTIL
from .kwg_json2field import kwg_json2field as Json2Field


class kwg_explore:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Linked Data Geographic Entities Property Enrichment"
        self.description = "Get the most common properties from a Knowledge Graph which supports GeoSPARQL based on the retrieved KG entities"

        self.sparqlQuery = kwg_sparqlquery()
        self.SPARQLUtil = UTIL()
        self.JSON2Field  = Json2Field()

        self.sparqlEndpoint = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"
        self.path_to_gpkg = "/var/local/QGIS/kwg_results.gpkg"
        self.layerName = "geo_results"

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

        self.retrievePropertyList()


    def retrievePropertyList(self):
        commonPropJSON = self.sparqlQuery.commonPropertyExploreQuery()
        self.extractPropertyJSON(commonPropJSON, self.commonPropertyURLDict, self.commonPropertyURLList, self.commonPropertyNameList,"common" )

        sosaPropJSON = self.sparqlQuery.commonSosaObsPropertyExploreQuery()
        self.extractPropertyJSON(sosaPropJSON, self.sosaPropertyURLDict, self.sosaPropertyURLList, self.sosaPropertyNameList, "sosa")

        inversePropJSON = self.sparqlQuery.inverseCommonPropertyExploreQuery()
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
        self.logger.info(propertyType + "_li: " + json.dumps(propertyDict))


    def extractPropertyJSON(self, propertyJSON, propertyDict, propertyURLList, propertyNameList, propertyType):
        resultsBindings = propertyJSON["results"]["bindings"]
        propertyDict = self.sparqlQuery.extractCommonPropertyJSON(
            resultsBindings,
            p_url_list=propertyURLList,
            p_name_list=propertyNameList,
            url_dict=propertyDict,
            p_var="p",
            plabel_var="plabel",
            numofsub_var="NumofSub")

        # self.logger.info(propertyType + "_url_li : " + str(propertyURLList))
        # self.logger.info(propertyType + "_name_li : " + str(propertyNameList))
        # self.logger.info(propertyType + "_dict : " + str(propertyDict))
        return


    def getPropertyLists(self):
        return self.commonPropertyNameList, self.commonPropertyURLList, self.sosaPropertyNameList, \
                self.sosaPropertyURLList, self.inversePropertyNameList, self.inversePropertyURLList


    def exectue(self):
        pass


if __name__ == '__main__':
    kwg_explore_object = kwg_explore()
    kwg_explore_object.loadIRIList()
    pass
