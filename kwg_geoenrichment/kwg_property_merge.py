from qgis._core import Qgis, QgsMessageLog

from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_util import kwg_util as UTIL
from .kwg_json2field import kwg_json2field as Json2Field



class MergeSingleNoFunctionalProperty(object):


    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Linked Data Single No Functional Property Merge"
        self.description = """The related seperated tables from Linked Data Location Entities Property Enrichment Tool have multivalue for each wikidata location because the coresponding property is not functional property.
        This Tool helps user to merge these multivalue to a single record and add it to original feature class sttribute table by using merge rules which are specified by users."""
        self.canRunInBackground = False
        self.kwg_sparqlquery = kwg_sparqlquery()
        self.kwg_util = UTIL()
        self.Json2Field = Json2Field()
        self.relatedTableFieldList = []
        self.relatedTableList = []
        self.relatedNoFunctionalPropertyURLList = []


    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True


    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        in_wikiplace_IRI = parameters[0]
        in_no_functional_property_list = parameters[1]
        in_related_table_list = parameters[2]
        in_merge_rule = parameters[3]
        in_cancatenate_delimiter = parameters[4]

        if in_wikiplace_IRI.altered:
            inputFeatureClassName = in_wikiplace_IRI.valueAsText
            lastIndexOFGDB = inputFeatureClassName.rfind("\\")
            featureClassName = inputFeatureClassName[(lastIndexOFGDB+1):]
            currentWorkspace = inputFeatureClassName[:lastIndexOFGDB]

            if currentWorkspace.endswith(".gdb") == False:
                messages.addErrorMessage("Please enter a feature class in file geodatabase for the input feature class.")
                raise arcpy.ExecuteError
            else:
                # if in_related_table.value:
                arcpy.env.workspace = currentWorkspace
                # out_location.value = currentWorkspace
                # out_points_name.value = featureClassName + "_noFunc_merge"
                # # check whether the input table are in the same file geodatabase as the input feature class
                # inputTableName = in_related_table.valueAsText
                # lastIndexOFTable = inputTableName.rfind("\\")
                # currentWorkspaceTable = inputTableName[:lastIndexOFTable]
                # if currentWorkspaceTable != currentWorkspace:
                #   messages.addErrorMessage("Please enter a table in the same file geodatabase as the input feature class.")
                #   raise arcpy.ExecuteError
                # else:
                #   if UTIL.detectRelationship(inputFeatureClassName, inputTableName):
                #       arcpy.AddMessage("The feature class and table are related!")
                self.relatedTableFieldList = []
                self.relatedTableList = []
                self.relatedNoFunctionalPropertyURLList = []

                self.relatedTableList = self.kwg_util.getRelatedTableFromFeatureClass(inputFeatureClassName)
                in_related_table_list.filter.list = self.relatedTableList

                # noFunctionalPropertyTable = []

                for relatedTable in self.relatedTableList:
                    fieldList = arcpy.ListFields(relatedTable)
                    if "origin" not in fieldList and "end" not in fieldList:
                        noFunctionalFieldName = fieldList[2].name
                        # arcpy.AddMessage("noFunctionalFieldName: {0}".format(noFunctionalFieldName))
                        self.relatedTableFieldList.append(noFunctionalFieldName)
                        # get the no functioal property URL from the firt row of this table field "propURL"
                        # propURL = arcpy.da.SearchCursor(relatedTable, ("propURL")).next()[0]

                        TableRelationshipClassList = self.kwg_util.getRelationshipClassFromTable(relatedTable)
                        propURL = arcpy.Describe(TableRelationshipClassList[0]).forwardPathLabel

                        self.relatedNoFunctionalPropertyURLList.append(propURL)

                in_no_functional_property_list.filter.list = self.relatedNoFunctionalPropertyURLList
                        # noFunctionalPropertyTable.append([noFunctionalFieldName, 'COUNT', relatedTable])
                        # MergeNoFunctionalProperty.relatedTableFieldList.append([noFunctionalFieldName, relatedTable, 'COUNT'])
                    # fieldmappings.addTable(relatedTable)
                    # fieldList = arcpy.ListFields(relatedTable)
                    # noFunctionalFieldName = fieldList[len(fieldList)-1].name
                    # arcpy.AddMessage("noFunctionalFieldName: {0}".format(noFunctionalFieldName))

                # in_stat_fields.values = noFunctionalPropertyTable

        if in_no_functional_property_list.altered:
            selectPropURL = in_no_functional_property_list.valueAsText
            selectIndex = self.relatedNoFunctionalPropertyURLList.index(selectPropURL)
            selectFieldName = self.relatedTableFieldList[selectIndex]
            selectTableName = self.relatedTableList[selectIndex]

            in_related_table_list.value = selectTableName

            currentDataType = self.kwg_util.getFieldDataTypeInTable(selectFieldName, selectTableName)
            if currentDataType in ['Single', 'Double', 'SmallInteger', 'Integer']:
                in_merge_rule.filter.list = ['SUM', 'MIN', 'MAX', 'STDEV', 'MEAN', 'COUNT', 'FIRST', 'LAST', 'CONCATENATE']
            else:
                in_merge_rule.filter.list = ['COUNT', 'FIRST', 'LAST', 'CONCATENATE']

        if in_related_table_list.altered:
            selectTableName = in_related_table_list.valueAsText
            selectIndex = self.relatedTableList.index(selectTableName)
            selectFieldName = self.relatedTableFieldList[selectIndex]
            selectPropURL = self.relatedNoFunctionalPropertyURLList[selectIndex]

            in_no_functional_property_list.value = selectPropURL

            currentDataType = self.kwg_util.getFieldDataTypeInTable(selectFieldName, selectTableName)
            if currentDataType in ['Single', 'Double', 'SmallInteger', 'Integer']:
                in_merge_rule.filter.list = ['SUM', 'MIN', 'MAX', 'STDEV', 'MEAN', 'COUNT', 'FIRST', 'LAST', 'CONCATENATE']
            else:
                in_merge_rule.filter.list = ['COUNT', 'FIRST', 'LAST', 'CONCATENATE']


        if in_merge_rule.valueAsText == "CONCATENATE":
            in_cancatenate_delimiter.enabled = True

        return


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return


    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_wikiplace_IRI = parameters[0]
        in_no_functional_property_list = parameters[1]
        in_related_table_list = parameters[2]
        in_merge_rule = parameters[3]
        in_cancatenate_delimiter = parameters[4]


        if in_wikiplace_IRI.value:
            inputFeatureClassName = in_wikiplace_IRI.valueAsText
            selectPropURL = in_no_functional_property_list.valueAsText
            selectTableName = in_related_table_list.valueAsText
            selectMergeRule = in_merge_rule.valueAsText

            selectIndex = self.relatedTableList.index(selectTableName)
            selectFieldName = self.relatedTableFieldList[selectIndex]

            QgsMessageLog.logMessage(("CurrentDataType: {0}".format(self.kwg_util.getFieldDataTypeInTable(selectFieldName, selectTableName))), "kwg_geoenrichment",  level=Qgis.info)

            QgsMessageLog.logMessage(("selectTableName: {0}".format(selectTableName)), "kwg_geoenrichment",  level=Qgis.info)

            QgsMessageLog.logMessage(("MergeSingleNoFunctionalProperty.relatedTableList: {0}".format(self.relatedTableList)), "kwg_geoenrichment",  level=Qgis.info)

            QgsMessageLog.logMessage(("MergeSingleNoFunctionalProperty.relatedTableList.index(selectTableName): {0}".format(self.relatedTableList.index(selectTableName))), "kwg_geoenrichment",  level=Qgis.info)

            noFunctionalPropertyDict = self.kwg_util.buildMultiValueDictFromNoFunctionalProperty(selectFieldName, selectTableName, URLFieldName = 'URL')

            if noFunctionalPropertyDict != -1:
                if selectMergeRule == 'CONCATENATE':
                    selectDelimiter = in_cancatenate_delimiter.valueAsText
                    delimiter = ','

                    # ['DASH', 'COMMA', 'VERTICAL BAR', 'TAB', 'SPACE']
                    if selectDelimiter == 'DASH':
                        delimiter = '-'
                    elif selectDelimiter == 'COMMA':
                        delimiter = ','
                    elif selectDelimiter == 'VERTICAL BAR':
                        delimiter = '|'
                    elif selectDelimiter == 'TAB':
                        delimiter = '   '
                    elif selectDelimiter == 'SPACE':
                        delimiter = ' '

                    self.kwg_util.appendFieldInFeatureClassByMergeRule(inputFeatureClassName, noFunctionalPropertyDict, selectFieldName, selectTableName, selectMergeRule, delimiter)
                else:
                    self.kwg_util.appendFieldInFeatureClassByMergeRule(inputFeatureClassName, noFunctionalPropertyDict, selectFieldName, selectTableName, selectMergeRule, '')
        return
