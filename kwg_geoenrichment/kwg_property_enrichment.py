
from qgis.PyQt.QtCore import QTranslator, QSettings, QCoreApplication, qVersion, QVariant
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QMenu, QInputDialog
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsFeature, QgsProject, QgsGeometry, \
    QgsCoordinateTransform, QgsCoordinateTransformContext, QgsMapLayer, \
    QgsFeatureRequest, QgsVectorLayer, QgsLayerTreeGroup, QgsRenderContext, \
    QgsCoordinateReferenceSystem, QgsWkbTypes, QgsMessageLog, Qgis, QgsFields, QgsField, QgsVectorFileWriter

import json

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


    def execute(self):
        inplaceIRIList = self.loadIRIList()
        kwg_sparqlquery_obj = kwg_sparqlquery()
        # get the direct common property
        commonPropertyJSONObj = kwg_sparqlquery_obj.commonPropertyQuery(inplaceIRIList=inplaceIRIList,
                                                                doSameAs=False)
        commonPropertyJSON = commonPropertyJSONObj["results"]["bindings"]
        return json.dumps(commonPropertyJSON)


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

        QgsMessageLog.logMessage(" | ".join(iriList), "kwg_geoenrichment", level=Qgis.Info)

        return iriList


if __name__ == '__main__':
    kwg_property_enrichment_object = kwg_property_enrichment()
    kwg_property_enrichment_object.loadIRIList()
    pass