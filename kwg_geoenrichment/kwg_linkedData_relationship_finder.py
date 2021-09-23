
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
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.firstPropertyLabelURLDict = dict()
        self.secondPropertyLabelURLDict = dict()
        self.thirdPropertyLabelURLDict = dict()
        self.fourthPropertyLabelURLDict = dict()
        self.label = "Linked Data Relationship Finder"
        self.description = """Getting a table of S-P-O triples for the relationships from locations features."""
        self.canRunInBackground = False
        self.SPARQLQuery = kwg_sparqlquery()
        self.SPARQLUtil = kwg_sparqlutil()
        self.Util = UTIL()
        self.JSON2Field = Json2Field()
        self.sparqlEndpoint = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"
        self.path_to_gpkg = "/var/local/QGIS/kwg_results.gpkg"
        self.layerName = "geo_results"


    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_sparql_endpoint = parameters[0]
        in_wikiplace_IRI = parameters[1]
        in_do_single_ent_start = parameters[2]
        in_single_ent = parameters[3]
        in_relation_degree = parameters[4]
        in_first_property_dir = parameters[5]
        in_first_property = parameters[6]
        in_second_property_dir = parameters[7]
        in_second_property = parameters[8]
        in_third_property_dir = parameters[9]
        in_third_property = parameters[10]
        in_fourth_property_dir = parameters[11]
        in_fourth_property = parameters[12]
        out_location = parameters[13]
        out_table_name = parameters[14]
        out_points_name = parameters[15]

        sparql_endpoint = in_sparql_endpoint.valueAsText

        relationDegree = int(in_relation_degree.valueAsText)
        outLocation = out_location.valueAsText
        outTableName = out_table_name.valueAsText
        outFeatureClassName = out_points_name.valueAsText
        outputTableName = os.path.join(outLocation, outTableName)
        outputFeatureClassName = os.path.join(outLocation, outFeatureClassName)

        # TODO: check for gpkg
        # # check whether outLocation is a file geodatabase
        # if outLocation.endswith(".gdb") == False:
        #     messages.addErrorMessage("Please enter a file geodatabase as the file location for output feature class.")
        #     raise arcpy.ExecuteError
        #     return
        # else:
        #     arcpy.env.workspace = outLocation

        # TODO: check for outputTableName
        # # check whether outputTableName or outputFeatureClassName already exist
        # if arcpy.Exists(outputTableName) or arcpy.Exists(outputFeatureClassName):
        #     messages.addErrorMessage("The output table or feature class already exists in current workspace!")
        #     raise arcpy.ExecuteError
        #     return

        if not in_do_single_ent_start.value:
            # if we use geo-entity feature class as start node
            inputFeatureClassName = in_wikiplace_IRI.valueAsText
            if not arcpy.Exists(inputFeatureClassName):
                arcpy.AddErrorMessage("The input feature class - {} - does not exist.".format(inputFeatureClassName))
                raise arcpy.ExecuteError
                return

            lastIndexOFGDB = inputFeatureClassName.rfind("\\")
            originFeatureClassName = inputFeatureClassName[(lastIndexOFGDB + 1):]

            # get all the IRI from input point feature class of wikidata places
            inplaceIRIList = []
            cursor = arcpy.SearchCursor(inputFeatureClassName)
            for row in cursor:
                inplaceIRIList.append(row.getValue("URL"))
        else:
            # we use single iri as the start node
            inplaceIRIList = [in_single_ent.valueAsText]

        # get the user specified property URL and direction at each degree
        propertyDirectionList = []
        selectPropertyURLList = ["", "", "", ""]
        if in_first_property_dir.value and relationDegree >= 1:
            fristDirection = in_first_property_dir.valueAsText
            firstProperty = in_first_property.valueAsText
            if firstProperty == None:
                firstPropertyURL = ""
            else:
                firstPropertyURL = self.firstPropertyLabelURLDict[firstProperty]

            propertyDirectionList.append(fristDirection)
            selectPropertyURLList[0] = firstPropertyURL

        if in_second_property_dir.value and relationDegree >= 2:
            secondDirection = in_second_property_dir.valueAsText
            secondProperty = in_second_property.valueAsText
            if secondProperty == None:
                secondPropertyURL = ""
            else:
                secondPropertyURL = self.secondPropertyLabelURLDict[secondProperty]

            propertyDirectionList.append(secondDirection)
            selectPropertyURLList[1] = secondPropertyURL

        if in_third_property_dir.value and relationDegree >= 3:
            thirdDirection = in_third_property_dir.valueAsText
            thirdProperty = in_third_property.valueAsText
            if thirdProperty == None:
                thirdPropertyURL = ""
            else:
                thirdPropertyURL = self.thirdPropertyLabelURLDict[thirdProperty]

            propertyDirectionList.append(thirdDirection)
            selectPropertyURLList[2] = thirdPropertyURL

        if in_fourth_property_dir.value and relationDegree >= 4:
            fourthDirection = in_fourth_property_dir.valueAsText
            fourthProperty = in_fourth_property.valueAsText
            if fourthProperty == None:
                fourthPropertyURL = ""
            else:
                fourthPropertyURL = self.thirdPropertyLabelURLDict[fourthProperty]

            propertyDirectionList.append(fourthDirection)
            selectPropertyURLList[3] = fourthPropertyURL

        # arcpy.AddMessage("propertyDirectionList: {0}".format(propertyDirectionList))
        # arcpy.AddMessage("selectPropertyURLList: {0}".format(selectPropertyURLList))

        # for the direction list, change "BOTH" to "OROIGIN" and "DESTINATION"
        directionExpendedLists = UTIL.directionListFromBoth2OD(propertyDirectionList)
        tripleStore = dict()
        for currentDirectionList in directionExpendedLists:
            # get a list of triples for curent specified property path
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
                                                                                   sparql_endpoint=sparql_endpoint)

            triplePropertyURLList = []
            triplePropertyLabelList = []
            for jsonItem in triplePropertyLabelJSON:
                propertyURL = jsonItem["p"]["value"]
                triplePropertyURLList.append(propertyURL)
                propertyName = jsonItem["propertyLabel"]["value"]
                triplePropertyLabelList.append(propertyName)
        else:
            # TODO:
            triplePropertyLabelList = self.SPARQLUtil.make_prefixed_iri_batch(triplePropertyURLList)

        triplePropertyURLLabelDict = dict(zip(triplePropertyURLList, triplePropertyLabelList))

        # TODO: QGIS implementation
        # tripleStoreTable = arcpy.CreateTable_management(outLocation, outTableName)
        #
        # arcpy.AddField_management(tripleStoreTable, "Subject", "TEXT",
        #                           field_length=Json2Field.fieldLengthDecideByList([triple.s for triple in tripleStore]))
        # arcpy.AddField_management(tripleStoreTable, "Predicate", "TEXT",
        #                           field_length=Json2Field.fieldLengthDecideByList([triple.p for triple in tripleStore]))
        # arcpy.AddField_management(tripleStoreTable, "Object", "TEXT",
        #                           field_length=Json2Field.fieldLengthDecideByList([triple.o for triple in tripleStore]))
        # arcpy.AddField_management(tripleStoreTable, "Pred_Label", "TEXT",
        #                           field_length=Json2Field.fieldLengthDecideByList(
        #                               [triplePropertyURLLabelDict[triple.p] for triple in tripleStore]))
        # arcpy.AddField_management(tripleStoreTable, "Degree", "LONG")

        # # Create insert cursor for table
        # rows = arcpy.InsertCursor(tripleStoreTable)

        # for triple in tripleStore:
        #     row = rows.newRow()
        #     row.setValue("Subject", triple.s)
        #     row.setValue("Predicate", triple.p)
        #     row.setValue("Object", triple.o)
        #     row.setValue("Pred_Label", triplePropertyURLLabelDict[triple.p])
        #     row.setValue("Degree", tripleStore[triple])

        #     rows.insertRow(row)

        # insertCursor = arcpy.da.InsertCursor(tripleStoreTable,
        #                                      ['Subject', 'Predicate', "Object", 'Pred_Label', "Degree"])
        # for triple in tripleStore:
        #     try:
        #         row = (triple.s, triple.p, triple.o, triplePropertyURLLabelDict[triple.p], tripleStore[triple])
        #         insertCursor.insertRow(row)
        #     except Error:
        #         arcpy.AddMessage(row)
        #         arcpy.AddMessage("Error inserting triple data: {} {} {}".format(triple.s, triple.p, triple.o))
        # del insertCursor
        #
        # ArcpyViz.visualize_current_layer(out_path=tripleStoreTable)
        #
        # entitySet = set()
        # for triple in tripleStore:
        #     entitySet.add(triple.s)
        #     entitySet.add(triple.o)
        # # for triple in tripleStore:
        # #   entitySet.add(triple[0])
        # #   entitySet.add(triple[2])
        #
        # arcpy.AddMessage("entitySet: {}".format(entitySet))
        # # TODO:
        # placeJSON = self.SPARQLQuery.endPlaceInformationQuery(list(entitySet), sparql_endpoint=sparql_endpoint)
        #
        # arcpy.AddMessage("placeJSON: {}".format(placeJSON))
        #
        # # create a Shapefile/FeatuerClass for all geographic entities in the triplestore
        # Json2Field.createFeatureClassFromSPARQLResult(GeoQueryResult=placeJSON,
        #                                               out_path=outputFeatureClassName,
        #                                               inPlaceType="",
        #                                               selectedURL="",
        #                                               isDirectInstance=False,
        #                                               viz_res=True)
        # # Json2Field.creatPlaceFeatureClassFromJSON(placeJSON, outputFeatureClassName, None, "")
        #
        # # add their centrold point of each geometry
        # arcpy.AddField_management(outputFeatureClassName, "POINT_X", "DOUBLE")
        # arcpy.AddField_management(outputFeatureClassName, "POINT_Y", "DOUBLE")
        # arcpy.CalculateField_management(outputFeatureClassName, "POINT_X", "!SHAPE.CENTROID.X!", "PYTHON_9.3")
        # arcpy.CalculateField_management(outputFeatureClassName, "POINT_Y", "!SHAPE.CENTROID.Y!", "PYTHON_9.3")
        #
        # arcpy.env.workspace = outLocation
        #
        # originFeatureRelationshipClassName = outputFeatureClassName + "_" + outTableName + "_Origin" + "_RelClass"
        # arcpy.CreateRelationshipClass_management(outputFeatureClassName, outTableName,
        #                                          originFeatureRelationshipClassName, "SIMPLE",
        #                                          "S-P-O Link", "Origin of S-P-O Link",
        #                                          "FORWARD", "ONE_TO_MANY", "NONE", "URL", "Subject")
        #
        # endFeatureRelationshipClassName = outputFeatureClassName + "_" + outTableName + "_Destination" + "_RelClass"
        # arcpy.CreateRelationshipClass_management(outputFeatureClassName, outTableName, endFeatureRelationshipClassName,
        #                                          "SIMPLE",
        #                                          "S-P-O Link", "Destination of S-P-O Link",
        #                                          "FORWARD", "ONE_TO_MANY", "NONE", "URL", "Object")

        return


if __name__ == '__main__':

    pass
