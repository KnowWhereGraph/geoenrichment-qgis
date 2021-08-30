from collections import defaultdict
import statistics
from qgis._core import QgsMessageLog, Qgis

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


    def getFieldNameWithTable(self, propertyName, featureClassName, gpkgLocation):
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


    def isFieldNameInTable(self, fieldName, featureClassName, gpkgLocation):
        # fieldList = arcpy.ListFields(inputFeatureClassName)
        # TODO: QGIS implementation
        fieldList = []

        isfieldNameinFieldList = False
        for field in fieldList:
            if field.name == fieldName:
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


    def getFieldDataTypeInTable(self, fieldName, inputFeatureClassName):
        # fieldList = arcpy.ListFields(inputFeatureClassName)
        fieldList = []
        # TODO: implement qgis logic
        for field in fieldList:
            if field.name == fieldName:
                return field.type

        return -1


    def buildMultiValueDictFromNoFunctionalProperty(self, fieldName, tableName, URLFieldName='wikiURL'):
        # build a collections.defaultdict object to store the multivalue for each no-functional property's subject.
        # The subject "wikiURL" is the key, the corespnding property value in "fieldName" is the value
        if self.isFieldNameInTable(fieldName, tableName):
            noFunctionalPropertyDict = defaultdict(list)
            # fieldList = arcpy.ListFields(tableName)

            srows = None
            # TODO: write up QGIS logic
            # srows = arcpy.SearchCursor(tableName, '', '', '', '{0} A;{1} A'.format(URLFieldName, fieldName))
            for row in srows:
                foreignKeyValue = row.getValue(URLFieldName)
                noFunctionalPropertyValue = row.getValue(fieldName)
                # if from_field in ['Double', 'Float']:
                #     value = locale.format('%s', (row.getValue(from_field)))
                if noFunctionalPropertyValue is not None:
                    noFunctionalPropertyDict[foreignKeyValue].append(noFunctionalPropertyValue)

            return noFunctionalPropertyDict
        else:
            return -1


    def appendFieldInFeatureClassByMergeRule(self, inputFeatureClassName, noFunctionalPropertyDict, appendFieldName,
                                             relatedTableName, mergeRule, delimiter):
        # append a new field in inputFeatureClassName which will install the merged no-functional property value
        # noFunctionalPropertyDict: the collections.defaultdict object which stores the no-functional property value for each URL
        # appendFieldName: the field name of no-functional property in the relatedTableName
        # mergeRule: the merge rule the user selected, one of ['SUM', 'MIN', 'MAX', 'STDEV', 'MEAN', 'COUNT', 'FIRST', 'LAST']
        # delimiter: the optional paramter which define the delimiter of the cancatenate operation
        appendFieldType = ''
        appendFieldLength = 0
        # fieldList = arcpy.ListFields(relatedTableName)
        # TODO: write up QGIS logic
        fieldList = []

        for field in fieldList:
            if field.name == appendFieldName:
                appendFieldType = field.type
                if field.type == "String":
                    appendFieldLength = field.length
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

        if appendFieldType != "String":
            cursor = []
            # TODO: write up QGIS logic
            # cursor = arcpy.SearchCursor(relatedTableName)
            for row in cursor:
                rowValue = row.getValue(appendFieldName)
                if appendFieldLength < len(str(rowValue)):
                    appendFieldLength = len(str(rowValue))
        # subFieldName = appendFieldName[:5]
        # arcpy.AddMessage("subFieldName: {0}".format(subFieldName))

        # featureClassAppendFieldName = subFieldName + "_" + mergeRuleField
        featureClassAppendFieldName = appendFieldName + "_" + mergeRuleField
        newAppendFieldName = self.getFieldNameWithTable(featureClassAppendFieldName, inputFeatureClassName)
        if newAppendFieldName != -1:
            if mergeRule == 'COUNT':
                # arcpy.AddField_management(inputFeatureClassName, newAppendFieldName, "SHORT")
                # TODO: write up QGIS logic
                pass
            elif mergeRule == 'STDEV' or mergeRule == 'MEAN':
                # arcpy.AddField_management(inputFeatureClassName, newAppendFieldName, "DOUBLE")
                # TODO: write up QGIS logic
                pass
            elif mergeRule == 'CONCATENATE':
                # get the maximum number of values for current property: maxNumOfValue
                # maxNumOfValue * field.length = the length of new append field
                maxNumOfValue = 1
                for key in noFunctionalPropertyDict:
                    if maxNumOfValue < len(noFunctionalPropertyDict[key]):
                        maxNumOfValue = len(noFunctionalPropertyDict[key])

                # arcpy.AddField_management(inputFeatureClassName, newAppendFieldName, 'TEXT',
                #                           field_length=
                #                           appendFieldLength * maxNumOfValue)
                # TODO: write up QGIS logic
                pass


            else:
                if appendFieldType == "String":
                    # arcpy.AddField_management(inputFeatureClassName, newAppendFieldName, appendFieldType,
                    #                           field_length=appendFieldLength)
                    # TODO: write up QGIS logic
                    pass
                else:
                    # arcpy.AddField_management(inputFeatureClassName, newAppendFieldName, appendFieldType)
                    # TODO: write up QGIS logic
                    pass

            if self.isFieldNameInTable("URL", inputFeatureClassName):
                urows = None
                # urows = arcpy.UpdateCursor(inputFeatureClassName)
                # TODO: write up QGIS logic
                pass
                for row in urows:
                    foreignKeyValue = row.getValue("URL")
                    noFunctionalPropertyValueList = noFunctionalPropertyDict[foreignKeyValue]
                    if len(noFunctionalPropertyValueList) != 0:
                        rowValue = ""
                        # if mergeRule in ['STDEV', 'MEAN']:
                        #     if appendFieldType in ['Single', 'Double']:
                        #         if mergeRule == 'MEAN':
                        #             rowValue = numpy.average(noFunctionalPropertyValueList)
                        #         elif mergeRule == 'STDEV':
                        #             rowValue = numpy.std(noFunctionalPropertyValueList)
                        #     else:
                        #         arcpy.AddError("The {0} data type of Field {1} does not support {2} merge rule".format(appendFieldType, appendFieldName, mergeRule))
                        #         raise arcpy.ExecuteError
                        # elif mergeRule in ['SUM', 'MIN', 'MAX']:
                        #     if appendFieldType in ['Single', 'Double', 'SmallInteger', 'Integer']:
                        #         if mergeRule == 'SUM':
                        #             rowValue = numpy.sum(noFunctionalPropertyValueList)
                        #         elif mergeRule == 'MIN':
                        #             rowValue = numpy.amin(noFunctionalPropertyValueList)
                        #         elif mergeRule == 'MAX':
                        #             rowValue = numpy.amax(noFunctionalPropertyValueList)
                        #     else:
                        #         arcpy.AddError("The {0} data type of Field {1} does not support {2} merge rule".format(appendFieldType, appendFieldName, mergeRule))
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

                        row.setValue(newAppendFieldName, rowValue)
                        urows.updateRow(row)
