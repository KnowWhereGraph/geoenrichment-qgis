from collections import OrderedDict

from .kwg_util import kwg_util

import math

class kwf_json2field:

    def __init__(self):
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









