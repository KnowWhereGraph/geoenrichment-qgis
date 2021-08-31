import json
from collections import OrderedDict, namedtuple
from decimal import Decimal

from PyQt5.QtCore import QVariant
from qgis._core import QgsVectorLayer, QgsMessageLog, Qgis, QgsField, QgsFields, QgsFeature, QgsGeometry, \
    QgsVectorFileWriter, QgsProject

from .kwg_util import kwg_util

import math

class kwg_json2field:

    def __init__(self):
        self.kwgUtil = kwg_util()
        pass

    def createFeatureClassFromSPARQLResult(self, GeoQueryResult, out_path="", inPlaceType="", selectedURL="",
                                           isDirectInstance=False, viz_res=True):
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

        UTIL = kwg_util()
        # a set of unique WKT for each found places
        placeIRISet = set()
        placeList = []
        geom_type = None
        for idx, item in enumerate(GeoQueryResult):
            wkt_literal = item["wkt"]["value"]
            # for now, make sure all geom has the same geometry type
            if idx == 0:
                geom_type = UTIL.get_geometry_type_from_wkt(wkt_literal)
            else:
                assert geom_type == UTIL.get_geometry_type_from_wkt(wkt_literal)

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

        if len(placeList) == 0:
            # arcpy.AddMessage("No {0} within the provided polygon can be finded!".format(inPlaceType))
            pass
        else:

            if out_path == None:
                pass
                # arcpy.AddMessage("No data will be added to the map document.")
                # pythonaddins.MessageBox("No data will be added to the map document.", "Warning Message", 0)
            else:
                # geo_feature_class = arcpy.CreateFeatureclass_management(
                #     os.path.dirname(out_path),
                #     os.path.basename(out_path),
                #     geometry_type=geom_type,
                #     spatial_reference=arcpy.SpatialReference(4326))

                labelFieldLength = self.fieldLengthDecide(GeoQueryResult, "placeLabel")
                # arcpy.AddMessage("labelFieldLength: {0}".format(labelFieldLength))

                urlFieldLength = self.fieldLengthDecide(GeoQueryResult, "place")
                # arcpy.AddMessage("urlFieldLength: {0}".format(urlFieldLength))

                if isDirectInstance == False:
                    classFieldLength = self.fieldLengthDecide(GeoQueryResult, "placeFlatType")
                else:
                    classFieldLength = len(selectedURL) + 50
                # arcpy.AddMessage("classFieldLength: {0}".format(classFieldLength))

                # # add field to this point feature class
                # arcpy.AddField_management(geo_feature_class, "Label", "TEXT", field_length=labelFieldLength)
                # arcpy.AddField_management(geo_feature_class, "URL", "TEXT", field_length=urlFieldLength)
                # arcpy.AddField_management(geo_feature_class, "Class", "TEXT", field_length=classFieldLength)
                #
                # insertCursor = arcpy.da.InsertCursor(out_path, ['URL', 'Label', "Class", 'SHAPE@WKT', ])
                # for item in placeList:
                #     place_iri, label, type_iri, wkt_literal = item
                #     wkt = wkt_literal.replace("<http://www.opengis.net/def/crs/OGC/1.3/CRS84>", "")
                #     try:
                #         insertCursor.insertRow((place_iri, label, type_iri, wkt))
                #     except Error:
                #         arcpy.AddMessage("Error inserting geo data: {} {} {}".format(place_iri, label, type_iri))
                #
                # del insertCursor
                #
                # if viz_res:
                #     ArcpyViz.visualize_current_layer(out_path)
        return


    def createQGISFeatureClassFromSPARQLResult(self, GeoQueryResult, out_path="/var/local/QGIS/kwg_results.gpkg", feat_class="geo_Result",inPlaceType="", selectedURL="",
                                           isDirectInstance=False, ifaceObj=None):
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

        layerFields = QgsFields()
        layerFields.append(QgsField('place_iri', QVariant.String))
        layerFields.append(QgsField('label', QVariant.String))
        layerFields.append(QgsField('type_iri', QVariant.String))

        for idx, item in enumerate(GeoQueryResult):
            wkt_literal = item["wkt"]["value"]
            # for now, make sure all geom has the same geometry type
            if idx == 0:
                geom_type = self.kwgUtil.get_geometry_type_from_wkt(wkt_literal)
            else:
                assert geom_type == self.kwgUtil.get_geometry_type_from_wkt(wkt_literal)

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

        vl = QgsVectorLayer(geom_type+"?crs=epsg:4326", feat_class, "memory")
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
                options.layerName = feat_class
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                context = QgsProject.instance().transformContext()
                error = QgsVectorFileWriter.writeAsVectorFormatV2(vl, out_path, context, options)
                ifaceObj.addVectorLayer(out_path, feat_class, 'ogr')

        return error[0] == QgsVectorFileWriter.NoError


    def fieldLengthDecide(self, jsonBindingObject, fieldName):
        # This option is only applicable on fields of type text or blob
        fieldType = self.fieldDataTypeDecide(jsonBindingObject, fieldName)
        if fieldType != "TEXT":
            # you do not need field length
            return -1
        else:
            maxLength = 30
            for jsonItem in jsonBindingObject:
                textLength = len(jsonItem[fieldName]["value"])
                if textLength > maxLength:
                    maxLength = textLength

            interval = 200

            for field_len in range(interval, 2000 + 1, interval):
                if maxLength < field_len:
                    return field_len
            return int(math.ceil(maxLength * 1.0 / interval) * interval)


    def fieldDataTypeDecide(self, jsonBindingObject, fieldName):
        # jsonBindingObject: a list object which is jsonObject.json()["results"]["bindings"]
        # fieldName: the name of the property/field in the JSON object thet what to evaluate
        # return the Field data type given a JSONItem for one property, return -1 if the field is about geometry and bnode
        dataTypeSet = set()
        for jsonItem in jsonBindingObject:
            dataTypeSet.add(self.getLinkedDataType(jsonItem, fieldName))

        dataTypeList = list(dataTypeSet)
        dataTypeCountDict = dict(zip(dataTypeList, [0] * len(dataTypeList)))

        for jsonItem in jsonBindingObject:
            dataTypeCountDict[self.getLinkedDataType(jsonItem, fieldName)] += 1

        dataTypeCountOrderDict = OrderedDict(sorted(dataTypeCountDict.items(), key=lambda t: t[1]))
        majorityDataType = next(reversed(dataTypeCountOrderDict))
        majorityFieldDataType = self.urlDataType2FieldDataType(majorityDataType)

        return majorityFieldDataType


    def urlDataType2FieldDataType(self, urlDataType):
        # urlDataType: url string date geometry int double float bnode
        # get a data type of Linked Data Literal (see getLinkedDataType), return a data type for field in arcgis Table View
        if urlDataType == "uri":
            return "TEXT"
        elif urlDataType == "string":
            return "TEXT"
        elif urlDataType == "date":
            return "DATE"
        elif urlDataType == "geometry":
            return -1
        elif urlDataType == "int":
            return "LONG"
        elif urlDataType == "double":
            return "DOUBLE"
        elif urlDataType == "float":
            return "FLOAT"
        elif urlDataType == "bnode":
            return -1
        else:
            return "TEXT"


    def getLinkedDataType(self, jsonBindingObjectItem, propertyName):
        # according the the property name of this jsonBindingObjectItem, return the meaningful dataType
        rdfDataType = jsonBindingObjectItem[propertyName]["type"]
        if rdfDataType == "uri":
            return "uri"
        elif "literal" in rdfDataType:
            if "datatype" not in jsonBindingObjectItem[propertyName]:
                return "string"
            else:
                specifiedDataType = jsonBindingObjectItem[propertyName]["datatype"]
                if specifiedDataType == "http://www.w3.org/2001/XMLSchema#date":
                    return "date"
                elif specifiedDataType == "http://www.openlinksw.com/schemas/virtrdf#Geometry":
                    return "geometry"
                elif specifiedDataType == "http://www.w3.org/2001/XMLSchema#integer" or specifiedDataType == "http://www.w3.org/2001/XMLSchema#nonNegativeInteger":
                    return "int"
                elif specifiedDataType == "http://www.w3.org/2001/XMLSchema#double":
                    return "double"
                elif specifiedDataType == "http://www.w3.org/2001/XMLSchema#float":
                    return "float"
                else:
                    return "string"
        elif rdfDataType == "bnode":
            return "bnode"
        else:
            return "string"


    def buildDictFromJSONToModifyTable(self, jsonBindingObject, keyPropertyName, valuePropertyName):
        valuePropertyList = []
        keyPropertyList = []
        for jsonItem in jsonBindingObject:
            valuePropertyList.append(jsonItem[valuePropertyName]["value"])
            keyPropertyList.append(jsonItem[keyPropertyName]["value"])

        keyValueDict = dict(zip(keyPropertyList, valuePropertyList))
        # QgsMessageLog.logMessage("keyValueDict: " + json.dumps(keyValueDict),
        #                          "kwg_geoenrichment", level=Qgis.Info)
        return keyValueDict


    def dataTypeCast(fieldValue, fieldDataType):
        # according to the field data type, cast the data into corresponding data type
        if fieldDataType == "TEXT":
            return fieldValue
        elif fieldDataType == "DATE":
            return fieldValue
        elif fieldDataType == "LONG":
            return int(fieldValue)
        elif fieldDataType == "DOUBLE":
            return Decimal(fieldValue)
        elif fieldDataType == "FLOAT":
            return float(fieldValue)


    def createMappingTableFromJSON(self, jsonBindingObject, keyPropertyName,
                                   valuePropertyName, valuePropertyURL,
                                   keyPropertyFieldName, isInverse, isSubDivisionTable, featureClassName="geo_results", outputLocation="", ifaceObj=None):


        currentValuePropertyName = self.kwgUtil.getPropertyName(valuePropertyURL)

        # currentValuePropertyName = SPARQLUtil.make_prefixed_iri(valuePropertyURL)
        if isInverse == True:
            currentValuePropertyName = "is_" + currentValuePropertyName + "_Of"
        if isSubDivisionTable == True:
            currentValuePropertyName = "subDivisionIRI"
        tableName = keyPropertyFieldName + "_" + currentValuePropertyName

        QgsMessageLog.logMessage(tableName,
                                 "kwg_geoenrichment", level=Qgis.Info)


        # TODO:  implement QGIS logic
        # tablePath = Json2Field.getNoExistTableNameInWorkspace(outputLocation, tableName)
        valuePropertyFieldType = self.fieldDataTypeDecide(jsonBindingObject, valuePropertyName)

        layerFields = QgsFields()
        layerFields.append(QgsField(keyPropertyFieldName, QVariant.String))
        if valuePropertyFieldType == "TEXT":
            layerFields.append(QgsField(currentValuePropertyName, QVariant.String))

        else:
            layerFields.append(QgsField(currentValuePropertyName))

        vl = QgsVectorLayer("POLYGON" + "?crs=epsg:4326", tableName, "memory")
        pr = vl.dataProvider()
        pr.addAttributes(layerFields)
        vl.updateFields()

        PropertyValue = namedtuple("PropertyValue", ["key", "value"])
        propertyValueSet = set()
        for jsonItem in jsonBindingObject:
            pair = PropertyValue(key=jsonItem[keyPropertyName]["value"], value=jsonItem[valuePropertyName]["value"])
            propertyValueSet.add(pair)

        propertyValueList = list(propertyValueSet)

        if outputLocation == None:
            QgsMessageLog.logMessage("No data will be added to the map document.", level=Qgis.Info)
        else:

            for item in propertyValueList:
                feat = QgsFeature()

                # TODO: handle the CRS
                # feat.setGeometry(self.transformSourceCRStoDestinationCRS(geom, src=4326, dest=3857))

                feat.setAttributes([item.key, item.value])
                pr.addFeature(feat)
            vl.updateExtents()

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.layerName = tableName
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            context = QgsProject.instance().transformContext()
            error = QgsVectorFileWriter.writeAsVectorFormatV2(vl, outputLocation, context, options)
            ifaceObj.addVectorLayer(outputLocation, tableName, 'ogr')

        return error[0] == QgsVectorFileWriter.NoError


    def addFieldInTableByMapping(self, jsonBindingObject, keyPropertyName, valuePropertyName, keyPropertyFieldName, valuePropertyURL, isInverse, featureClassName="geo_results", gpkgLocation=""):
        # according to the json object from sparql query which contains the mapping from keyProperty to valueProperty, add field in the Table
        # change the field name if there is already a field which has the same name in table
        # jsonBindingObject: the json object from sparql query which contains the mapping from keyProperty to valueProperty, ex. functionalPropertyJSON
        # keyPropertyName: the name of keyProperty in JSON object, ex. wikidataSub
        # valuePropertyName: the name of valueProperty in JSON object, ex. o
        # keyPropertyFieldName:  the name of the field which stores the value of keyProperty, ex. URL
        # valuePropertyURL: tatomhe URL of valueProperty, we use it to get the field name of valueProperty, ex. functionalProperty
        # isInverse: Boolean variable indicates whether the value we get is the subject value or object value of valuePropertyURL

        keyValueDict = self.buildDictFromJSONToModifyTable(jsonBindingObject, keyPropertyName, valuePropertyName)

        currentValuePropertyName = self.kwgUtil.getPropertyName(valuePropertyURL)
        # currentValuePropertyName = SPARQLUtil.make_prefixed_iri(valuePropertyURL)
        if isInverse == True:
            currentValuePropertyName = "is_" + currentValuePropertyName + "_Of"

        gpkg_places_layer = gpkgLocation + "|layername=%s" % (featureClassName)

        vlayer = QgsVectorLayer(gpkg_places_layer, "geo_results", "ogr")

        if not vlayer.isValid():
            QgsMessageLog.logMessage("Error reading the table",
                                     "kwg_geoenrichment", level=Qgis.Warning)
            return 0

        # TODO: temp set up; move to permanent
        # currentFieldName = self.kwgUtil.getFieldNameWithTable(currentValuePropertyName, featureClassName, gpkgLocation)
        currentFieldName =currentValuePropertyName
        if currentFieldName == -1:
            # messages.addWarningMessage("The table of current feature class has more than 10 fields for property name {0}.".format(currentValuePropertyName))
            pass
        else:

            # add one field for each functional property in input feature class
            fieldType = self.fieldDataTypeDecide(jsonBindingObject, valuePropertyName)
            # arcpy.AddMessage("fieldType: {0}".format(fieldType))
            if fieldType == "TEXT":
                fieldLength = self.fieldLengthDecide(jsonBindingObject, valuePropertyName)
                pr = vlayer.dataProvider()
                pr.addAttributes([QgsField(currentFieldName, QVariant.String)])
                vlayer.updateFields()
            else:
                pr = vlayer.dataProvider()
                pr.addAttributes([QgsField(currentFieldName)])
                vlayer.updateFields()

            selected_feature = vlayer.getFeatures()
            QgsMessageLog.logMessage(
                "Features selected, beginning editing the values for those features " ,
                "kwg_geoenrichment", level=Qgis.Info)
            vlayer.startEditing()

            for feature in selected_feature:
                currentKeyPropertyValue = feature[keyPropertyFieldName]
                if currentKeyPropertyValue in keyValueDict:
                    feature[currentFieldName] = keyValueDict[currentKeyPropertyValue]
                vlayer.updateFeature(feature)
            vlayer.commitChanges()

        return 1

