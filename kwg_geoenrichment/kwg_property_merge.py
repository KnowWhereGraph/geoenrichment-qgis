

from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_util import kwg_util as UTIL
from .kwg_json2field import kwg_json2field as Json2Field





class MergeSingleNoFunctionalProperty(object):
    relatedTableFieldList = []
    relatedTableList = []
    relatedNoFunctionalPropertyURLList = []

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Linked Data Single No Functional Property Merge"
        self.description = """The related seperated tables from Linked Data Location Entities Property Enrichment Tool have multivalue for each wikidata location because the coresponding property is not functional property.
        This Tool helps user to merge these multivalue to a single record and add it to original feature class sttribute table by using merge rules which are specified by users."""
        self.canRunInBackground = False
        self.kwg_sparqlquery = kwg_sparqlquery()
        self.kwg_util = UTIL()
        self.Json2Field = Json2Field()

    def getParameterInfo(self):
        """Define parameter definitions"""
        # The input Feature class which is the output of LinkedDataAnalysis Tool, "URL" column should be included in the attribute table
        in_wikiplace_IRI = arcpy.Parameter(
            displayName="Input wikidata location entities Feature Class",
            name="in_wikiplace_IRI",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # in_wikiplace_IRI.filter.list = ["Point"]

        in_no_functional_property_list = arcpy.Parameter(
            displayName="List of No-Functional Properties of Current Feature Class",
            name="in_no_functional_property_list",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        in_no_functional_property_list.filter.type = "ValueList"
        in_no_functional_property_list.filter.list = []

        in_related_table_list = arcpy.Parameter(
            displayName="List of Related Tables",
            name="in_related_table_list",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        in_related_table_list.filter.type = "ValueList"
        in_related_table_list.filter.list = []

        in_merge_rule = arcpy.Parameter(
        displayName='List of Merge Rules',
        name='in_merge_rule',
        datatype='GPString',
        parameterType='Required',
        direction='Input')

        in_merge_rule.filter.type = "ValueList"
        in_merge_rule.filter.list = ['SUM', 'MIN', 'MAX', 'STDEV', 'MEAN', 'COUNT', 'FIRST', 'LAST', 'CONCATENATE']

        in_cancatenate_delimiter = arcpy.Parameter(
        displayName='The delimiter of cancatenating fields',
        name='in_cancatenate_delimiter',
        datatype='GPString',
        parameterType='Optional',
        direction='Input')

        in_cancatenate_delimiter.filter.type = "ValueList"
        in_cancatenate_delimiter.filter.list = ['DASH', 'COMMA', 'VERTICAL BAR', 'TAB', 'SPACE']
        in_cancatenate_delimiter.enabled = False

        params = [in_wikiplace_IRI, in_no_functional_property_list, in_related_table_list, in_merge_rule, in_cancatenate_delimiter]

        return params

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
                MergeSingleNoFunctionalProperty.relatedTableFieldList = []
                MergeSingleNoFunctionalProperty.relatedTableList = []
                MergeSingleNoFunctionalProperty.relatedNoFunctionalPropertyURLList = []

                MergeSingleNoFunctionalProperty.relatedTableList = UTIL.getRelatedTableFromFeatureClass(inputFeatureClassName)
                in_related_table_list.filter.list = MergeSingleNoFunctionalProperty.relatedTableList

                # noFunctionalPropertyTable = []

                for relatedTable in MergeSingleNoFunctionalProperty.relatedTableList:
                    fieldList = arcpy.ListFields(relatedTable)
                    if "origin" not in fieldList and "end" not in fieldList:
                        noFunctionalFieldName = fieldList[2].name
                        arcpy.AddMessage("noFunctionalFieldName: {0}".format(noFunctionalFieldName))
                        MergeSingleNoFunctionalProperty.relatedTableFieldList.append(noFunctionalFieldName)
                        # get the no functioal property URL from the firt row of this table field "propURL"
                        # propURL = arcpy.da.SearchCursor(relatedTable, ("propURL")).next()[0]

                        TableRelationshipClassList = UTIL.getRelationshipClassFromTable(relatedTable)
                        propURL = arcpy.Describe(TableRelationshipClassList[0]).forwardPathLabel

                        MergeSingleNoFunctionalProperty.relatedNoFunctionalPropertyURLList.append(propURL)

                in_no_functional_property_list.filter.list = MergeSingleNoFunctionalProperty.relatedNoFunctionalPropertyURLList
                        # noFunctionalPropertyTable.append([noFunctionalFieldName, 'COUNT', relatedTable])
                        # MergeNoFunctionalProperty.relatedTableFieldList.append([noFunctionalFieldName, relatedTable, 'COUNT'])
                    # fieldmappings.addTable(relatedTable)
                    # fieldList = arcpy.ListFields(relatedTable)
                    # noFunctionalFieldName = fieldList[len(fieldList)-1].name
                    # arcpy.AddMessage("noFunctionalFieldName: {0}".format(noFunctionalFieldName))

                # in_stat_fields.values = noFunctionalPropertyTable

        if in_no_functional_property_list.altered:
            selectPropURL = in_no_functional_property_list.valueAsText
            selectIndex = MergeSingleNoFunctionalProperty.relatedNoFunctionalPropertyURLList.index(selectPropURL)
            selectFieldName = MergeSingleNoFunctionalProperty.relatedTableFieldList[selectIndex]
            selectTableName = MergeSingleNoFunctionalProperty.relatedTableList[selectIndex]

            in_related_table_list.value = selectTableName

            currentDataType = UTIL.getFieldDataTypeInTable(selectFieldName, selectTableName)
            if currentDataType in ['Single', 'Double', 'SmallInteger', 'Integer']:
                in_merge_rule.filter.list = ['SUM', 'MIN', 'MAX', 'STDEV', 'MEAN', 'COUNT', 'FIRST', 'LAST', 'CONCATENATE']
            # elif currentDataType in ['SmallInteger', 'Integer']:
            #   in_merge_rule.filter.list = ['SUM', 'MIN', 'MAX', 'COUNT', 'FIRST', 'LAST']
            else:
                in_merge_rule.filter.list = ['COUNT', 'FIRST', 'LAST', 'CONCATENATE']

        if in_related_table_list.altered:
            selectTableName = in_related_table_list.valueAsText
            selectIndex = MergeSingleNoFunctionalProperty.relatedTableList.index(selectTableName)
            selectFieldName = MergeSingleNoFunctionalProperty.relatedTableFieldList[selectIndex]
            selectPropURL = MergeSingleNoFunctionalProperty.relatedNoFunctionalPropertyURLList[selectIndex]

            in_no_functional_property_list.value = selectPropURL

            currentDataType = UTIL.getFieldDataTypeInTable(selectFieldName, selectTableName)
            if currentDataType in ['Single', 'Double', 'SmallInteger', 'Integer']:
                in_merge_rule.filter.list = ['SUM', 'MIN', 'MAX', 'STDEV', 'MEAN', 'COUNT', 'FIRST', 'LAST', 'CONCATENATE']
            # elif currentDataType in ['SmallInteger', 'Integer']:
            #   in_merge_rule.filter.list = ['SUM', 'MIN', 'MAX', 'COUNT', 'FIRST', 'LAST']
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

            selectIndex = MergeSingleNoFunctionalProperty.relatedTableList.index(selectTableName)
            selectFieldName = MergeSingleNoFunctionalProperty.relatedTableFieldList[selectIndex]

            arcpy.AddMessage("CurrentDataType: {0}".format(UTIL.getFieldDataTypeInTable(selectFieldName, selectTableName)))

            arcpy.AddMessage("selectTableName: {0}".format(selectTableName))

            arcpy.AddMessage("MergeSingleNoFunctionalProperty.relatedTableList: {0}".format(MergeSingleNoFunctionalProperty.relatedTableList))

            arcpy.AddMessage("MergeSingleNoFunctionalProperty.relatedTableList.index(selectTableName): {0}".format(MergeSingleNoFunctionalProperty.relatedTableList.index(selectTableName)))

            lastIndexOFGDB = inputFeatureClassName.rfind("\\")
            currentWorkspace = inputFeatureClassName[:lastIndexOFGDB]

            if currentWorkspace.endswith(".gdb") == False:
                messages.addErrorMessage("Please enter a feature class in file geodatabase for the input feature class.")
                raise arcpy.ExecuteError
            else:
                # if in_related_table.value:
                arcpy.env.workspace = currentWorkspace


                noFunctionalPropertyDict = UTIL.buildMultiValueDictFromNoFunctionalProperty(selectFieldName, selectTableName, URLFieldName = 'URL')

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

                        UTIL.appendFieldInFeatureClassByMergeRule(inputFeatureClassName, noFunctionalPropertyDict, selectFieldName, selectTableName, selectMergeRule, delimiter)
                    else:
                        UTIL.appendFieldInFeatureClassByMergeRule(inputFeatureClassName, noFunctionalPropertyDict, selectFieldName, selectTableName, selectMergeRule, '')


        return
