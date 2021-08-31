from collections import defaultdict
import statistics

from PyQt5.QtCore import QVariant
from qgis._core import QgsMessageLog, Qgis, QgsVectorLayer, QgsField

from .kwg_sparqlutil import kwg_sparqlutil


class kwg_util:


    def __init__(self):
        pass


    def get_geometry_type_from_wkt(wkt):
        if "POINT".lower() in wkt.lower():
            return "POINT"
        elif "MULTIPOINT".lower() in wkt.lower():
            return "MULTIPOINT"
        elif "LINESTRING".lower() in wkt.lower():
            return "POLYLINE"
        elif "MULTILINESTRING".lower() in wkt.lower():
            return "POLYLINE"
        elif "POLYGON".lower() in wkt.lower():
            return "POLYGON"
        elif "MULTIPOLYGON".lower() in wkt.lower():
            return "POLYGON"
        else:
            raise Exception("Unrecognized geometry type: {}".format(wkt))


    def extractCommonPropertyJSON(self, commonPropertyJSON,
                                  p_url_list=[], p_name_list=[], url_dict={},
                                  p_var="p", plabel_var="pLabel", numofsub_var="NumofSub"):
        SPARQLUtil = kwg_sparqlutil()
        for jsonItem in commonPropertyJSON:
            propertyURL = jsonItem[p_var]["value"]
            if propertyURL not in p_url_list:
                p_url_list.append(propertyURL)
                label = ""
                if plabel_var in jsonItem:
                    label = jsonItem[plabel_var]["value"]
                if label.strip() == "":
                    label = SPARQLUtil.make_prefixed_iri(propertyURL)
                propertyName = f"""{label} [{jsonItem[numofsub_var]["value"]}]"""
                p_name_list.append(propertyName)

        url_dict = dict(zip(p_name_list, p_url_list))

        return url_dict


    def getPropertyName(self, propertyURL):
        # give a URL of property, get the property name (without prefix)
        if "#" in propertyURL:
            lastIndex = propertyURL.rfind("#")
            propertyName = propertyURL[(lastIndex + 1):]
        else:
            lastIndex = propertyURL.rfind("/")
            propertyName = propertyURL[(lastIndex + 1):]

        return propertyName


    def getFieldNameWithTable(self, propertyName, featureClassName, gpkgLocation='/var/local/QGIS/kwg_results.gpkg'):
        # give a property Name which have been sliced by getPropertyName(propertyURL)
        # decide whether its lengh is larger than 10
        # decide whether it is already in the feature class table
        # return the final name of this field, if return -1, that mean the field name has more than 10 times in this table, you just do nothing
        # if len(propertyName) > 10:
        #     propertyName = propertyName[:9]

        isfieldNameinTable = self.isFieldNameInTable(propertyName, featureClassName, gpkgLocation)
        if isfieldNameinTable == False:
            return propertyName
        else:
            return self.changeFieldNameWithTable(propertyName, featureClassName, gpkgLocation)


    def isFieldNameInTable(self, fieldName, featureClassName, gpkgLocation='/var/local/QGIS/kwg_results.gpkg'):

        # read layer and check for existing fields
        gpkg_places_layer = gpkgLocation + "|layername=%s" % (featureClassName)
        vlayer = QgsVectorLayer(gpkg_places_layer, featureClassName, "ogr")
        prov = vlayer.dataProvider()
        fieldList = [field.name() for field in prov.fields()]

        isfieldNameinFieldList = False
        for field in fieldList:
            if field == fieldName:
                isfieldNameinFieldList = True
                break

        return isfieldNameinFieldList


    def changeFieldNameWithTable(self, propertyName, featureClassName, gpkgLocation):
        for i in range(1, 10):
            propertyName = propertyName[:(len(propertyName) - 1)] + str(i)
            isfieldNameinTable = self.isFieldNameInTable(propertyName, featureClassName, gpkgLocation)
            if isfieldNameinTable == False:
                return propertyName

        return -1


    def getFieldDataTypeInTable(self, fieldName, featureClassName, gpkgLocation='/var/local/QGIS/kwg_results.gpkg'):

        # read layer and check for existing fields
        gpkg_places_layer = gpkgLocation + "|layername=%s" % (featureClassName)
        vlayer = QgsVectorLayer(gpkg_places_layer, featureClassName, "ogr")
        prov = vlayer.dataProvider()
        fieldList = [field.name() for field in prov.fields()]

        for field in fieldList:
            if field.name() == fieldName:
                return field.typeName()

        return -1


    def buildMultiValueDictFromNoFunctionalProperty(self, fieldName, tableName, URLFieldName='wikiURL', featureClassName="geo_results", gpkgLocation="/var/local/QGIS/kwg_results.gpkg"):
        # build a collections.defaultdict object to store the multivalue for each no-functional property's subject.
        # The subject "wikiURL" is the key, the corespnding property value in "fieldName" is the value
        if self.isFieldNameInTable(fieldName, tableName):
            noFunctionalPropertyDict = defaultdict(list)
            # fieldList = arcpy.ListFields(tableName)

            gpkg_places_layer = gpkgLocation + "|layername=%s" % (tableName)
            vlayer = QgsVectorLayer(gpkg_places_layer, tableName, "ogr")

            if not vlayer.isValid():
                srows  = None
            else:
                for feature in vlayer.getFeatures():
                    row = feature.attributes()
                    foreignKeyValue = row[1]
                    noFunctionalPropertyValue = row[2]

                    if noFunctionalPropertyValue is not None:
                        noFunctionalPropertyDict[foreignKeyValue].append(noFunctionalPropertyValue)

            return noFunctionalPropertyDict
        else:
            return -1


    def appendFieldInFeatureClassByMergeRule(self, inputFeatureClassName, noFunctionalPropertyDict, appendFieldName,
                                             relatedTableName, mergeRule, delimiter, gpkgLocation="/var/local/QGIS/kwg_results.gpkg"):
        # append a new field in inputFeatureClassName which will install the merged no-functional property value
        # noFunctionalPropertyDict: the collections.defaultdict object which stores the no-functional property value for each URL
        # appendFieldName: the field name of no-functional property in the relatedTableName
        # mergeRule: the merge rule the user selected, one of ['SUM', 'MIN', 'MAX', 'STDEV', 'MEAN', 'COUNT', 'FIRST', 'LAST']
        # delimiter: the optional paramter which define the delimiter of the cancatenate operation
        appendFieldType = ''

        # readthe layer from the geopackage
        gpkg_places_layer = gpkgLocation + "|layername=%s" % (inputFeatureClassName)
        vlayer = QgsVectorLayer(gpkg_places_layer, "geo_results", "ogr")

        if not vlayer.isValid():
            QgsMessageLog.logMessage("Error reading the table",
                                     "kwg_geoenrichment", level=Qgis.Warning)
            return 0

        # get the field list
        prov = vlayer.dataProvider()
        fieldList = [field.name() for field in prov.fields()]

        for field in fieldList:
            if field == appendFieldName:
                appendFieldType = field.typeName()
                break

        mergeRuleField = ''
        if mergeRule == 'SUM':
            mergeRuleField = 'SUM'
        elif mergeRule == 'MIN':
            mergeRuleField = 'MIN'
        elif mergeRule == 'MAX':
            mergeRuleField = 'MAX'
        elif mergeRule == 'STDEV':
            mergeRuleField = 'STD'
        elif mergeRule == 'MEAN':
            mergeRuleField = 'MEN'
        elif mergeRule == 'COUNT':
            mergeRuleField = 'COUNT'
        elif mergeRule == 'FIRST':
            mergeRuleField = 'FIRST'
        elif mergeRule == 'LAST':
            mergeRuleField = 'LAST'
        elif mergeRule == 'CONCATENATE':
            mergeRuleField = 'CONCAT'

        # featureClassAppendFieldName = subFieldName + "_" + mergeRuleField
        featureClassAppendFieldName = appendFieldName + "_" + mergeRuleField
        newAppendFieldName = self.getFieldNameWithTable(featureClassAppendFieldName, inputFeatureClassName)
        if newAppendFieldName != -1:
            if mergeRule == 'COUNT':
                prov.addAttributes([QgsField(newAppendFieldName, QVariant.Int)])
                vlayer.updateFields()
            elif mergeRule == 'STDEV' or mergeRule == 'MEAN':
                # arcpy.AddField_management(inputFeatureClassName, newAppendFieldName, "DOUBLE")
                prov.addAttributes([QgsField(newAppendFieldName, QVariant.Double)])
                vlayer.updateFields()
            else:
                prov.addAttributes([QgsField(newAppendFieldName, QVariant.String)])
                vlayer.updateFields()

            if self.isFieldNameInTable("place_iri", inputFeatureClassName):

                vlayer.startEditing()
                for feature in vlayer.getFeatures():
                    foreignKeyValue = feature["place_iri"]
                    noFunctionalPropertyValueList = noFunctionalPropertyDict[foreignKeyValue]
                    if len(noFunctionalPropertyValueList) != 0:
                        rowValue = ""

                        if mergeRule in ['STDEV', 'MEAN', 'SUM', 'MIN', 'MAX']:
                            if appendFieldType in ['Single', 'Double', 'SmallInteger', 'Integer']:
                                if mergeRule == 'MEAN':
                                    rowValue = statistics.mean(noFunctionalPropertyValueList)
                                elif mergeRule == 'STDEV':
                                    rowValue = statistics.stdev(noFunctionalPropertyValueList)
                                elif mergeRule == 'SUM':
                                    rowValue = sum(noFunctionalPropertyValueList)
                                    pass
                                elif mergeRule == 'MIN':
                                    rowValue = min(noFunctionalPropertyValueList)
                                elif mergeRule == 'MAX':
                                    rowValue = max(noFunctionalPropertyValueList)
                            else:
                                QgsMessageLog.logMessage("The {0} data type of Field {1} does not support {2} merge rule".format(appendFieldType,
                                                                                                        appendFieldName,
                                                                                                        mergeRule), "kwg_geoenrichment", level=Qgis.Warning)
                        elif mergeRule in ['COUNT', 'FIRST', 'LAST']:
                            if mergeRule == 'COUNT':
                                rowValue = len(noFunctionalPropertyValueList)
                            elif mergeRule == 'FIRST':
                                rowValue = noFunctionalPropertyValueList[0]
                            elif mergeRule == 'LAST':
                                rowValue = noFunctionalPropertyValueList[len(noFunctionalPropertyValueList) - 1]
                        elif mergeRule == 'CONCATENATE':
                            value = ""
                            if appendFieldType in ['String']:
                                rowValue = delimiter.join(
                                    sorted(set([val for val in noFunctionalPropertyValueList if not value is None])))
                            else:
                                rowValue = delimiter.join(sorted(
                                    set([str(val) for val in noFunctionalPropertyValueList if not value is None])))

                        feature[newAppendFieldName] = rowValue

                        vlayer.updateFeature(feature)
                vlayer.commitChanges()

        return 1
