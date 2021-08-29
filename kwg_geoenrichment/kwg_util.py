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

        isfieldNameinTable = self.isFieldNameInTable(propertyName, inputFeatureClassName)
        if isfieldNameinTable == False:
            return propertyName
        else:
            return self.changeFieldNameWithTable(propertyName, inputFeatureClassName)


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
            isfieldNameinTable = self.isFieldNameInTable(propertyName, inputFeatureClassName)
            if isfieldNameinTable == False:
                return propertyName

        return -1
