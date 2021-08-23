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

