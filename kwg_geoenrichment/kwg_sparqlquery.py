import json
import logging
from collections import namedtuple

from .kwg_sparqlutil import kwg_sparqlutil

from qgis.core import QgsMessageLog, Qgis

class kwg_sparqlquery:

    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # or whatever
        self.sparqlUTIL = kwg_sparqlutil()
        handler = logging.FileHandler(
            '/var/local/QGIS/kwg_geoenrichment.log', 'w',
            'utf-8')  # or whatever
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')  # or whatever
        handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
        self.logger.addHandler(handler)

    def EventTypeSPARQLQuery( self, sparql_endpoint="http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"):
        """
        Performs a HTTP request to retrieve all the event / place
        type as defined by the GEOSPARQL quer
        Args:
            sparql_endpoint:
        """
        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        query = queryPrefix + """
            select distinct ?entityType ?entityTypeLabel
            where
            {
                ?entity rdf:type ?entityType .
                ?entity geo:hasGeometry ?aGeom .
                ?entityType rdfs:label ?entityTypeLabel
            }
        """
        #
        # QgsMessageLog.logMessage(query, "kwg_explore", level=Qgis.Info)

        GeoQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                    sparql_endpoint=sparql_endpoint,
                                                    doInference=False,
                                                    request_method="get")
        GeoQueryResult = GeoQueryResult["results"]["bindings"]

        # QgsMessageLog.logMessage(json.dumps(GeoQueryResult), "kwg_ldrf", level=Qgis.Info)

        return GeoQueryResult


    def TypeAndGeoSPARQLQuery(self, query_geo_wkt, selectedURL="",
                              isDirectInstance=False,
                              geosparql_func=["geo:sfIntersects"],
                              sparql_endpoint="http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"):
        '''
        Format GeoSPARQL query by given query_geo_wkt and type
        Args:
            query_geo_wkt: the wkt literal
            selectedURL: the user spercified type IRI
            isDirectInstance: True: use placeFlatType as the type of geo-entity
                              False: use selectedURL as the type of geo-entity
            geosparql_func: a list of geosparql functions
            sparql_endpoint:
        '''
        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()


        query = queryPrefix + """
                select distinct ?place ?placeLabel ?placeFlatType ?wkt
                where
                {

                    ?place geo:hasGeometry ?geometry .
                    ?place rdfs:label ?placeLabel .
                    ?geometry geo:asWKT ?wkt.
                    ?place rdf:type ?placeFlatType .
                    { '''
                <http://www.opengis.net/def/crs/OGC/1.3/CRS84>
                """ + query_geo_wkt + """
                '''^^geo:wktLiteral """ + geosparql_func[0] + """  ?geometry .}
            """
        if len(geosparql_func) == 2:
            query += """ union
                    { '''
                <http://www.opengis.net/def/crs/OGC/1.3/CRS84>
                """ + query_geo_wkt + """
                '''^^geo:wktLiteral  """ + geosparql_func[1] + """   ?geometry  .}
            """

        if selectedURL != None and selectedURL != "":
            # query = queryPrefix + """
            #     select distinct ?place ?placeLabel ?placeFlatType ?wkt
            #     where
            #     {

            #         ?place geo:hasGeometry ?geometry .
            #         ?place rdfs:label ?placeLabel .
            #         ?geometry geo:asWKT ?wkt.
            #         FILTER (""" + geosparql_func[0] + """('''
            #     <http://www.opengis.net/def/crs/OGC/1.3/CRS84>
            #     """ + query_geo_wkt + """
            #     '''^^geo:wktLiteral, ?wkt)
            #     )
            # """
            if isDirectInstance == False:
                query += """
                    ?place rdf:type ?placeFlatType.
                    ?placeFlatType rdfs:subClassOf* <""" + selectedURL + """>."""
            else:
                query += """?place rdf:type  <""" + selectedURL + """>."""

                # show results ordered by distance
            query += """}"""
        else:
            # query = queryPrefix + """
            #     select distinct ?place ?placeLabel ?placeFlatType ?wkt
            #     where
            #     {

            #         ?place geo:hasGeometry ?geometry .
            #         ?place rdfs:label ?placeLabel .
            #         ?geometry geo:asWKT ?wkt.
            #         FILTER (""" + geosparql_func[0] + """('''
            #     <http://www.opengis.net/def/crs/OGC/1.3/CRS84>
            #     """ + query_geo_wkt + """
            #     '''^^geo:wktLiteral, ?wkt))
            #     }
            # """
            query += "}"

        # QgsMessageLog.logMessage(query, "kwg_explore", level=Qgis.Info)
        GeoQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                    sparql_endpoint=sparql_endpoint,
                                                    doInference=False)
        GeoQueryResult = GeoQueryResult["results"]["bindings"]
        return GeoQueryResult


    def commonPropertyQuery(self, inplaceIRIList, sparql_endpoint="http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire", doSameAs=True):


        queryPrefix = self.sparqlUTIL.make_sparql_prefix()

        iri_list = ""
        for IRI in inplaceIRIList:
            iri_list = iri_list + "<" + IRI + "> \n"

        if sparql_endpoint == kwg_sparqlutil._WIKIDATA_SPARQL_ENDPOINT:
            commonPropertyQuery = queryPrefix + """SELECT ?p ?prop ?propLabel ?NumofSub WHERE
                                        {
                                            {
                                                SELECT ?prop ?p (COUNT(DISTINCT ?s) AS ?NumofSub) WHERE
                                                {

                                                    hint:Query hint:optimizer "None" .

                                                    ?s ?p ?o .
                                                    ?prop wikibase:directClaim ?p .

                                                    VALUES ?s
                                                    {
            """
            commonPropertyQuery += iri_list
            commonPropertyQuery += """
                                                    }
                                                }  GROUP BY ?prop ?p
                                            }

                                            SERVICE wikibase:label {
                                                bd:serviceParam wikibase:language "en" .
                                            }

                                        } ORDER BY DESC (?NumofSub)
            """

        else:
            if doSameAs:
                commonPropertyQuery = queryPrefix + """select distinct ?p (count(distinct ?s) as ?NumofSub)
                                            where
                                            {
                                            ?s owl:sameAs ?wikidataSub.
                                            ?s ?p ?o.
                                            VALUES ?wikidataSub
                                            {"""
            else:
                commonPropertyQuery = queryPrefix + """select distinct ?p (count(distinct ?s) as ?NumofSub)
                                            where
                                            {
                                            ?s ?p ?o.
                                            VALUES ?s
                                            {"""
            commonPropertyQuery += iri_list

            commonPropertyQuery += """
                                            }
                                            }
                                            group by ?p
                                            order by DESC(?NumofSub)
                                            """

        # QgsMessageLog.logMessage(commonPropertyQuery, "kwg_geoenrichment", level=Qgis.Info)
        res_json = self.sparqlUTIL.sparql_requests(query=commonPropertyQuery,
                                              sparql_endpoint=sparql_endpoint,
                                              doInference=False)
        return res_json


    def commonSosaObsPropertyQuery(self, inplaceIRIList, sparql_endpoint='https://dbpedia.org/sparql', doSameAs=False):
        queryPrefix = self.sparqlUTIL.make_sparql_prefix()

        commonPropertyQuery = queryPrefix + """select distinct ?p ?pLabel (count(distinct ?s) as ?NumofSub)
                                        where {
                                        ?s sosa:isFeatureOfInterestOf ?obscol .
                                        ?obscol sosa:hasMember ?obs.
                                        ?obs sosa:observedProperty ?p .
                                        OPTIONAL {?p rdfs:label ?pLabel . }
                                        VALUES ?s
                                        {
                                        """
        for IRI in inplaceIRIList:
            commonPropertyQuery = commonPropertyQuery + "<" + IRI + "> \n"

        commonPropertyQuery = commonPropertyQuery + """
                                        }
                                        }
                                        group by ?p ?pLabel
                                        order by DESC(?NumofSub)
                                        """

        res_json = self.sparqlUTIL.sparql_requests(query=commonPropertyQuery,
                                              sparql_endpoint=sparql_endpoint,
                                              doInference=False)
        return res_json


    def inverseCommonPropertyQuery(self, inplaceIRIList, sparql_endpoint='https://dbpedia.org/sparql', doSameAs=True):
        queryPrefix = self.sparqlUTIL.make_sparql_prefix()

        if doSameAs:
            commonPropertyQuery = queryPrefix + """select distinct ?p (count(distinct ?s) as ?NumofSub)
                                            where
                                            { ?s owl:sameAs ?wikidataSub.
                                            ?o ?p ?s.
                                            VALUES ?wikidataSub
                                            {"""
        else:
            commonPropertyQuery = queryPrefix + """select distinct ?p (count(distinct ?s) as ?NumofSub)
                                        where
                                        {
                                        ?o ?p ?s.
                                        VALUES ?s
                                        {"""
        for IRI in inplaceIRIList:
            commonPropertyQuery = commonPropertyQuery + "<" + IRI + "> \n"

        commonPropertyQuery = commonPropertyQuery + """
                                        }
                                        }
                                        group by ?p
                                        order by DESC(?NumofSub)
                                        """

        res_json = self.sparqlUTIL.sparql_requests(query=commonPropertyQuery,
                                              sparql_endpoint=sparql_endpoint,
                                              doInference=False)
        return res_json


    def functionalPropertyQuery(self, propertyURLList, sparql_endpoint='https://dbpedia.org/sparql'):
        # give a list of property, get a sublist which are functional property

        # send a SPARQL query to DBpedia endpoint to test whether the user selected properties are functionalProperty
        jsonBindingObject = []
        i = 0
        while i < len(propertyURLList):
            if i + 50 > len(propertyURLList):
                propertyURLSubList = propertyURLList[i:]
            else:
                propertyURLSubList = propertyURLList[i:(i + 50)]

            queryPrefix = self.sparqlUTIL.make_sparql_prefix()

            isFuncnalPropertyQuery = queryPrefix + """select ?property
                            where
                            { ?property a owl:FunctionalProperty.
                            VALUES ?property
                            {"""
            for propertyURL in propertyURLSubList:
                isFuncnalPropertyQuery = isFuncnalPropertyQuery + "<" + propertyURL + "> \n"

            isFuncnalPropertyQuery = isFuncnalPropertyQuery + """
                            }
                            }
                            """

            res_json = self.sparqlUTIL.sparql_requests(query=isFuncnalPropertyQuery,
                                                  sparql_endpoint=sparql_endpoint,
                                                  doInference=False)
            jsonBindingObject.extend(res_json["results"]["bindings"])

            i = i + 50
            self.logger.info(str(jsonBindingObject))
        return jsonBindingObject


    def propertyValueQuery(self, inplaceIRIList, propertyURL, sparql_endpoint='https://dbpedia.org/sparql', doSameAs=True):
        # according to a list of wikidata IRI (inplaceIRIList), get the value for a specific property (propertyURL) from DBpedia
        jsonBindingObject = []
        i = 0
        while i < len(inplaceIRIList):
            if i + 50 > len(inplaceIRIList):
                inplaceIRISubList = inplaceIRIList[i:]
            else:
                inplaceIRISubList = inplaceIRIList[i:(i + 50)]
            queryPrefix = self.sparqlUTIL.make_sparql_prefix()

            if doSameAs:
                PropertyValueQuery = queryPrefix + """select ?wikidataSub ?o
                                where
                                { ?s owl:sameAs ?wikidataSub.
                                ?s <""" + propertyURL + """> ?o.
                                VALUES ?wikidataSub
                                {
                                """
            else:
                PropertyValueQuery = queryPrefix + """select ?wikidataSub ?o
                                where
                                {
                                ?wikidataSub <""" + propertyURL + """> ?o.
                                VALUES ?wikidataSub
                                {
                                """
            for IRI in inplaceIRISubList:
                PropertyValueQuery += "<" + IRI + "> \n"

            PropertyValueQuery += """
                            }
                            }
                            """

            res_json = self.sparqlUTIL.sparql_requests(query=PropertyValueQuery,
                                                  sparql_endpoint=sparql_endpoint,
                                                  doInference=False)
            jsonBindingObject.extend(res_json["results"]["bindings"])

            i = i + 50

        return jsonBindingObject
        # return PropertyValueSparqlRequest.json()


    def checkGeoPropertyquery(self, inplaceIRIList, propertyURL, sparql_endpoint='https://dbpedia.org/sparql', doSameAs=True):
        # according to a list of wikidata IRI (inplaceIRIList), get the value for a specific property (propertyURL) from DBpedia
        jsonBindingObject = []
        i = 0
        while i < len(inplaceIRIList):
            if i + 50 > len(inplaceIRIList):
                inplaceIRISubList = inplaceIRIList[i:]
            else:
                inplaceIRISubList = inplaceIRIList[i:(i + 50)]
            queryPrefix = self.sparqlUTIL.make_sparql_prefix()
            PropertyValueQuery = queryPrefix + """select (count(?geometry) as ?cnt)
                                where
                                {
                                """
            if doSameAs:
                PropertyValueQuery += """ ?s owl:sameAs ?wikidataSub.
                                ?s <""" + propertyURL + """> ?place.
                                """
            else:
                PropertyValueQuery += """
                                ?wikidataSub <""" + propertyURL + """> ?place.
                                """
            PropertyValueQuery += """
                                ?place geo:hasGeometry ?geometry .
                                """
            PropertyValueQuery += """
                                VALUES ?wikidataSub
                                {
                                """
            for IRI in inplaceIRISubList:
                PropertyValueQuery += "<" + IRI + "> \n"

            PropertyValueQuery += """
                            }
                            }
                            """

            res_json = self.sparqlUTIL.sparql_requests(query=PropertyValueQuery,
                                                  sparql_endpoint=sparql_endpoint,
                                                  doInference=False)

            jsonBindingObject.extend(res_json["results"]["bindings"])

            i = i + 50

        return jsonBindingObject


    def twoDegreePropertyValueWKTquery(self, inplaceIRIList, propertyURL, sparql_endpoint='https://dbpedia.org/sparql',
                                       doSameAs=True):
        # according to a list of wikidata IRI (inplaceIRIList), get the value for a specific property (propertyURL) from DBpedia
        jsonBindingObject = []
        i = 0
        while i < len(inplaceIRIList):
            if i + 50 > len(inplaceIRIList):
                inplaceIRISubList = inplaceIRIList[i:]
            else:
                inplaceIRISubList = inplaceIRIList[i:(i + 50)]
            queryPrefix = self.sparqlUTIL.make_sparql_prefix()
            PropertyValueQuery = queryPrefix + """select distinct ?place ?placeLabel ?placeFlatType ?wkt
                                where
                                {
                                """
            if doSameAs:
                PropertyValueQuery += """ ?s owl:sameAs ?wikidataSub.
                                ?s <""" + propertyURL + """> ?place.
                                """
            else:
                PropertyValueQuery += """
                                ?wikidataSub <""" + propertyURL + """> ?place.
                                """
            PropertyValueQuery += """
                                ?place geo:hasGeometry ?geometry .
                                ?place rdfs:label ?placeLabel .
                                ?geometry geo:asWKT ?wkt.
                                ?place rdf:type ?placeFlatType.
                                """
            PropertyValueQuery += """
                                VALUES ?wikidataSub
                                {
                                """
            for IRI in inplaceIRISubList:
                PropertyValueQuery += "<" + IRI + "> \n"

            PropertyValueQuery += """
                            }
                            }
                            """

            res_json = self.sparqlUTIL.sparql_requests(query=PropertyValueQuery,
                                                  sparql_endpoint=sparql_endpoint,
                                                  doInference=False)
            jsonBindingObject.extend(res_json["results"]["bindings"])

            i = i + 50

        return jsonBindingObject


    def sosaObsPropertyValueQuery(self, inplaceIRIList, propertyURL,
                                  sparql_endpoint='https://dbpedia.org/sparql', doSameAs=False):
        # according to a list of wikidata IRI (inplaceIRIList), get the value for a specific property (propertyURL) from DBpedia
        jsonBindingObject = []
        i = 0
        while i < len(inplaceIRIList):
            if i + 50 > len(inplaceIRIList):
                inplaceIRISubList = inplaceIRIList[i:]
            else:
                inplaceIRISubList = inplaceIRIList[i:(i + 50)]
            queryPrefix = self.sparqlUTIL.make_sparql_prefix()

            PropertyValueQuery = queryPrefix + """select ?wikidataSub ?o
                            where
                            {
                            ?wikidataSub sosa:isFeatureOfInterestOf ?obscol .
                            ?obscol sosa:hasMember ?obs.
                            ?obs sosa:observedProperty <""" + propertyURL + """> .
                            ?obs sosa:hasSimpleResult ?o.
                            VALUES ?wikidataSub
                            {
                            """
            for IRI in inplaceIRISubList:
                PropertyValueQuery += "<" + IRI + "> \n"

            PropertyValueQuery += """
                            }
                            }
                            """

            res_json = self.sparqlUTIL.sparql_requests(query=PropertyValueQuery,
                                                  sparql_endpoint=sparql_endpoint,
                                                  doInference=False)
            jsonBindingObject.extend(res_json["results"]["bindings"])

            i = i + 50

        return jsonBindingObject


    def extractCommonPropertyJSON(self, commonPropertyJSON,
                                  p_url_list=[], p_name_list=[], url_dict={},
                                  p_var="p", plabel_var="pLabel", numofsub_var="NumofSub"):
        for jsonItem in commonPropertyJSON:
            propertyURL = jsonItem[p_var]["value"]
            if propertyURL not in p_url_list:
                p_url_list.append(propertyURL)
                label = ""
                if plabel_var in jsonItem:
                    label = jsonItem[plabel_var]["value"]
                if label.strip() == "":
                    label = self.sparqlUTIL.make_prefixed_iri(propertyURL)
                if numofsub_var is None:
                    propertyName = label
                else:
                    propertyName = f"""{label} [{jsonItem[numofsub_var]["value"]}]"""
                p_name_list.append(propertyName)

        url_dict = dict(zip(p_name_list, p_url_list))

        return url_dict


    def relFinderTripleQuery(self,inplaceIRIList, propertyDirectionList, selectPropertyURLList,
                             sparql_endpoint=None):

        if sparql_endpoint is None:
            sparql_endpoint = self.sparqlUTIL._WIKIDATA_SPARQL_ENDPOINT
        # get the triple set in the specific degree path from the inplaceIRIList
        # inplaceIRIList: the URL list of wikidata locations
        # propertyDirectionList: the list of property direction, it has at most 4 elements, the length is the path degree. The element value is from ["ORIGIN", "DESTINATION"]
        # selectPropertyURLList: the selected peoperty URL list, it always has 4 elements, "" if no property has been selected

        # get the selected parameter
        # selectParam = "?place ?p1 ?o1 ?p2 ?o2 ?p3 ?o3 ?p4 ?o4"

        selectParam = "?place "
        if len(propertyDirectionList) > 0:
            if selectPropertyURLList[0] == "":
                selectParam += "?p1 "

        selectParam += "?o1 "

        if len(propertyDirectionList) > 1:
            if selectPropertyURLList[1] == "":
                selectParam += "?p2 "

        selectParam += "?o2 "

        if len(propertyDirectionList) > 2:
            if selectPropertyURLList[2] == "":
                selectParam += "?p3 "

        selectParam += "?o3 "

        if len(propertyDirectionList) > 3:
            if selectPropertyURLList[3] == "":
                selectParam += "?p4 "

        selectParam += "?o4 "

        jsonBindingObject = []
        i = 0
        while i < len(inplaceIRIList):
            if i + 50 > len(inplaceIRIList):
                inplaceIRISubList = inplaceIRIList[i:]
            else:
                inplaceIRISubList = inplaceIRIList[i:(i+50)]

            queryPrefix = self.sparqlUTIL.make_sparql_prefix()

            relFinderPropertyQuery = queryPrefix + """SELECT distinct """ + selectParam + """
                            WHERE {"""

            if len(propertyDirectionList) > 0:
                if selectPropertyURLList[0] == "":
                    # if propertyDirectionList[0] == "BOTH":
                    #     relFinderPropertyQuery += """{?place ?p1 ?o1.} UNION {?o1 ?p1 ?place.}\n"""
                    if propertyDirectionList[0] == "ORIGIN":
                        relFinderPropertyQuery += """?place ?p1 ?o1.\n"""
                    elif propertyDirectionList[0] == "DESTINATION":
                        relFinderPropertyQuery += """?o1 ?p1 ?place.\n"""
                else:
                    # if propertyDirectionList[0] == "BOTH":
                    #     relFinderPropertyQuery += """{?place <"""+ selectPropertyURLList[0] + """> ?o1.} UNION {?o1 <"""+ selectPropertyURLList[0] + """> ?place.}\n"""
                    if propertyDirectionList[0] == "ORIGIN":
                        relFinderPropertyQuery += """?place <"""+ selectPropertyURLList[0] + """> ?o1.\n"""
                    elif propertyDirectionList[0] == "DESTINATION":
                        relFinderPropertyQuery += """?o1 <"""+ selectPropertyURLList[0] + """> ?place.\n"""

            if len(propertyDirectionList) > 1:
                if selectPropertyURLList[1] == "":
                    # if propertyDirectionList[1] == "BOTH":
                    #     relFinderPropertyQuery += """{?o1 ?p2 ?o2.} UNION {?o2 ?p2 ?o1.}\n"""
                    if propertyDirectionList[1] == "ORIGIN":
                        relFinderPropertyQuery += """?o1 ?p2 ?o2.\n"""
                    elif propertyDirectionList[1] == "DESTINATION":
                        relFinderPropertyQuery += """?o2 ?p2 ?o1.\n"""
                else:
                    # if propertyDirectionList[1] == "BOTH":
                    #     relFinderPropertyQuery += """{?o1 <"""+ selectPropertyURLList[1] + """> ?o2.} UNION {?o2 <"""+ selectPropertyURLList[1] + """> ?o1.}\n"""
                    if propertyDirectionList[1] == "ORIGIN":
                        relFinderPropertyQuery += """?o1 <"""+ selectPropertyURLList[1] + """> ?o2.\n"""
                    elif propertyDirectionList[1] == "DESTINATION":
                        relFinderPropertyQuery += """?o2 <"""+ selectPropertyURLList[1] + """> ?o1.\n"""

            if len(propertyDirectionList) > 2:
                if selectPropertyURLList[2] == "":
                    # if propertyDirectionList[2] == "BOTH":
                    #     relFinderPropertyQuery += """{?o2 ?p3 ?o3.} UNION {?o3 ?p3 ?o2.}\n"""
                    if propertyDirectionList[2] == "ORIGIN":
                        relFinderPropertyQuery += """?o2 ?p3 ?o3.\n"""
                    elif propertyDirectionList[2] == "DESTINATION":
                        relFinderPropertyQuery += """?o3 ?p3 ?o2.\n"""
                else:
                    # if propertyDirectionList[2] == "BOTH":
                    #     relFinderPropertyQuery += """{?o2 <"""+ selectPropertyURLList[2] + """> ?o3.} UNION {?o3 <"""+ selectPropertyURLList[2] + """> ?o2.}\n"""
                    if propertyDirectionList[2] == "ORIGIN":
                        relFinderPropertyQuery += """?o2 <"""+ selectPropertyURLList[2] + """> ?o3.\n"""
                    elif propertyDirectionList[2] == "DESTINATION":
                        relFinderPropertyQuery += """?o3 <"""+ selectPropertyURLList[2] + """> ?o2.\n"""

            if len(propertyDirectionList) > 3:
                if selectPropertyURLList[3] == "":
                    # if propertyDirectionList[3] == "BOTH":
                    #     relFinderPropertyQuery += """{?o3 ?p4 ?o4.} UNION {?o4 ?p4 ?o3.}\n"""
                    if propertyDirectionList[3] == "ORIGIN":
                        relFinderPropertyQuery += """?o3 ?p4 ?o4.\n"""
                    elif propertyDirectionList[3] == "DESTINATION":
                        relFinderPropertyQuery += """?o4 ?p4 ?o3.\n"""
                else:
                    # if propertyDirectionList[3] == "BOTH":
                    #     relFinderPropertyQuery += """{?o3 <"""+ selectPropertyURLList[3] + """> ?o4.} UNION {?o4 <"""+ selectPropertyURLList[3] + """> ?o3.}\n"""
                    if propertyDirectionList[3] == "ORIGIN":
                        relFinderPropertyQuery += """?o3 <"""+ selectPropertyURLList[3] + """> ?o4.\n"""
                    elif propertyDirectionList[3] == "DESTINATION":
                        relFinderPropertyQuery += """?o4 <"""+ selectPropertyURLList[3] + """> ?o3.\n"""




            relFinderPropertyQuery += """
                            VALUES ?place
                            {"""
            for IRI in inplaceIRISubList:
                relFinderPropertyQuery = relFinderPropertyQuery + "<" + IRI + "> \n"

            relFinderPropertyQuery = relFinderPropertyQuery + """
                            }
                            }
                            """

            res_json = self.sparqlUTIL.sparql_requests(query = relFinderPropertyQuery,
                                               sparql_endpoint = sparql_endpoint,
                                               doInference = False)
            jsonBindingObject.extend(res_json["results"]["bindings"])

            i = i + 50

        tripleStore = dict()
        Triple = namedtuple("Triple", ["s", "p", "o"])
        for jsonItem in jsonBindingObject:
            if len(propertyDirectionList) > 0:
                # triple = []
                if selectPropertyURLList[0] == "":
                    if propertyDirectionList[0] == "ORIGIN":
                        # relFinderPropertyQuery += """?place ?p1 ?o1.\n"""
                        currentTriple = Triple(s = jsonItem["place"]["value"], p = jsonItem["p1"]["value"], o = jsonItem["o1"]["value"])
                    elif propertyDirectionList[0] == "DESTINATION":
                        # relFinderPropertyQuery += """?o1 ?p1 ?place.\n"""
                        currentTriple = Triple(s = jsonItem["o1"]["value"], p = jsonItem["p1"]["value"], o = jsonItem["place"]["value"])
                        # triple = [jsonItem["o1"]["value"], jsonItem["p1"]["value"], jsonItem["place"]["value"]]
                else:
                    if propertyDirectionList[0] == "ORIGIN":
                        # relFinderPropertyQuery += """?place <"""+ selectPropertyURLList[0] + """> ?o1.\n"""
                        currentTriple = Triple(s = jsonItem["place"]["value"], p = selectPropertyURLList[0], o = jsonItem["o1"]["value"])
                        # triple = [jsonItem["place"]["value"], selectPropertyURLList[0], jsonItem["o1"]["value"]]
                    elif propertyDirectionList[0] == "DESTINATION":
                        # relFinderPropertyQuery += """?o1 <"""+ selectPropertyURLList[0] + """> ?place.\n"""
                        currentTriple = Triple(s = jsonItem["o1"]["value"], p = selectPropertyURLList[0], o = jsonItem["place"]["value"])
                        # triple = [jsonItem["o1"]["value"], selectPropertyURLList[0], jsonItem["place"]["value"]]

                if currentTriple not in tripleStore:
                    tripleStore[currentTriple] = 1
                else:
                    if tripleStore[currentTriple] > 1:
                        tripleStore[currentTriple] = 1


            if len(propertyDirectionList) > 1:
                # triple = []
                if selectPropertyURLList[1] == "":
                    if propertyDirectionList[1] == "ORIGIN":
                        # relFinderPropertyQuery += """?o1 ?p2 ?o2.\n"""
                        currentTriple = Triple(s = jsonItem["o1"]["value"], p = jsonItem["p2"]["value"], o = jsonItem["o2"]["value"])
                        # triple = [jsonItem["o1"]["value"], jsonItem["p2"]["value"], jsonItem["o2"]["value"]]
                    elif propertyDirectionList[1] == "DESTINATION":
                        # relFinderPropertyQuery += """?o2 ?p2 ?o1.\n"""
                        currentTriple = Triple(s = jsonItem["o2"]["value"], p = jsonItem["p2"]["value"], o = jsonItem["o1"]["value"])
                        # triple = [jsonItem["o2"]["value"], jsonItem["p2"]["value"], jsonItem["o1"]["value"]]
                else:
                    if propertyDirectionList[1] == "ORIGIN":
                        # relFinderPropertyQuery += """?o1 <"""+ selectPropertyURLList[1] + """> ?o2.\n"""
                        currentTriple = Triple(s = jsonItem["o1"]["value"], p = selectPropertyURLList[1], o = jsonItem["o2"]["value"])
                        # triple = [jsonItem["o1"]["value"], selectPropertyURLList[1], jsonItem["o2"]["value"]]
                    elif propertyDirectionList[1] == "DESTINATION":
                        # relFinderPropertyQuery += """?o2 <"""+ selectPropertyURLList[1] + """> ?o1.\n"""
                        currentTriple = Triple(s = jsonItem["o2"]["value"], p = selectPropertyURLList[1], o = jsonItem["o1"]["value"])
                        # triple = [jsonItem["o2"]["value"], selectPropertyURLList[1], jsonItem["o1"]["value"]]

                if currentTriple not in tripleStore:
                    tripleStore[currentTriple] = 2
                else:
                    if tripleStore[currentTriple] > 2:
                        tripleStore[currentTriple] = 2

            if len(propertyDirectionList) > 2:
                # triple = []
                if selectPropertyURLList[2] == "":
                    if propertyDirectionList[2] == "ORIGIN":
                        # relFinderPropertyQuery += """?o2 ?p3 ?o3.\n"""
                        currentTriple = Triple(s = jsonItem["o2"]["value"], p = jsonItem["p3"]["value"], o = jsonItem["o3"]["value"])
                        # triple = [jsonItem["o2"]["value"], jsonItem["p3"]["value"], jsonItem["o3"]["value"]]
                    elif propertyDirectionList[2] == "DESTINATION":
                        # relFinderPropertyQuery += """?o3 ?p3 ?o2.\n"""
                        currentTriple = Triple(s = jsonItem["o3"]["value"], p = jsonItem["p3"]["value"], o = jsonItem["o2"]["value"])
                        # triple = [jsonItem["o3"]["value"], jsonItem["p3"]["value"], jsonItem["o2"]["value"]]
                else:
                    if propertyDirectionList[2] == "ORIGIN":
                        # relFinderPropertyQuery += """?o2 <"""+ selectPropertyURLList[2] + """> ?o3.\n"""
                        currentTriple = Triple(s = jsonItem["o2"]["value"], p = selectPropertyURLList[2], o = jsonItem["o3"]["value"])
                        # triple = [jsonItem["o2"]["value"], selectPropertyURLList[2], jsonItem["o3"]["value"]]
                    elif propertyDirectionList[2] == "DESTINATION":
                        # relFinderPropertyQuery += """?o3 <"""+ selectPropertyURLList[2] + """> ?o2.\n"""
                        currentTriple = Triple(s = jsonItem["o3"]["value"], p = selectPropertyURLList[2], o = jsonItem["o2"]["value"])
                        # triple = [jsonItem["o3"]["value"], selectPropertyURLList[2], jsonItem["o2"]["value"]]

                if currentTriple not in tripleStore:
                    tripleStore[currentTriple] = 3
                else:
                    if tripleStore[currentTriple] > 3:
                        tripleStore[currentTriple] = 3

            if len(propertyDirectionList) > 3:
                triple = []
                if selectPropertyURLList[3] == "":
                    if propertyDirectionList[3] == "ORIGIN":
                        # relFinderPropertyQuery += """?o3 ?p4 ?o4.\n"""
                        currentTriple = Triple(s = jsonItem["o3"]["value"], p = jsonItem["p4"]["value"], o = jsonItem["o4"]["value"])
                        # triple = [jsonItem["o3"]["value"], jsonItem["p4"]["value"], jsonItem["o4"]["value"]]
                    elif propertyDirectionList[3] == "DESTINATION":
                        # relFinderPropertyQuery += """?o4 ?p4 ?o3.\n"""
                        currentTriple = Triple(s = jsonItem["o4"]["value"], p = jsonItem["p4"]["value"], o = jsonItem["o3"]["value"])
                        # triple = [jsonItem["o4"]["value"], jsonItem["p4"]["value"], jsonItem["o3"]["value"]]
                else:
                    if propertyDirectionList[3] == "ORIGIN":
                        # relFinderPropertyQuery += """?o3 <"""+ selectPropertyURLList[3] + """> ?o4.\n"""
                        currentTriple = Triple(s = jsonItem["o3"]["value"], p = selectPropertyURLList[3], o = jsonItem["o4"]["value"])
                        # triple = [jsonItem["o3"]["value"], selectPropertyURLList[3], jsonItem["o4"]["value"]]
                    elif propertyDirectionList[3] == "DESTINATION":
                        # relFinderPropertyQuery += """?o4 <"""+ selectPropertyURLList[3] + """> ?o3.\n"""
                        currentTriple = Triple(s = jsonItem["o4"]["value"], p = selectPropertyURLList[3], o = jsonItem["o3"]["value"])
                        # triple = [jsonItem["o4"]["value"], selectPropertyURLList[3], jsonItem["o3"]["value"]]

                if currentTriple not in tripleStore:
                    tripleStore[currentTriple] = 4

        return tripleStore


    def locationCommonPropertyLabelQuery(self, locationCommonPropertyURLList, sparql_endpoint = None):
        if sparql_endpoint is None:
            sparql_endpoint = self.sparqlUTIL._WIKIDATA_SPARQL_ENDPOINT

        jsonBindingObject = []
        i = 0
        while i < len(locationCommonPropertyURLList):
            if i + 50 > len(locationCommonPropertyURLList):
                propertyIRISubList = locationCommonPropertyURLList[i:]
            else:
                propertyIRISubList = locationCommonPropertyURLList[i:(i+50)]

            queryPrefix = self.sparqlUTIL.make_sparql_prefix()

            commonPropertyLabelQuery = queryPrefix + """select ?p ?propertyLabel
                            where
                            {
                            ?wdProperty wikibase:directClaim ?p.
                            SERVICE wikibase:label {bd:serviceParam wikibase:language "en". ?wdProperty rdfs:label ?propertyLabel.}
                            VALUES ?p
                            {"""
            for propertyURL in propertyIRISubList:
                commonPropertyLabelQuery = commonPropertyLabelQuery + "<" + propertyURL + "> \n"

            commonPropertyLabelQuery = commonPropertyLabelQuery + """
                            }
                            }
                            """
            res_json = self.sparqlUTIL.sparql_requests(query = commonPropertyLabelQuery,
                                       sparql_endpoint = sparql_endpoint,
                                       doInference = False)

            jsonBindingObject.extend(res_json["results"]["bindings"])


            i = i + 50
        return jsonBindingObject


    def relFinderCommonPropertyQuery(self, inplaceIRIList, relationDegree, propertyDirectionList, selectPropertyURLList,
                                     sparql_endpoint=None):

        if sparql_endpoint is None:
            sparql_endpoint = self.sparqlUTIL._WIKIDATA_SPARQL_ENDPOINT

        # get the property URL list in the specific degree path from the inplaceIRIList
        # inplaceIRIList: the URL list of wikidata locations
        # relationDegree: the degree of the property on the path the current query wants to get
        # propertyDirectionList: the list of property direction, it has at most 4 elements, the length is the path degree. The element value is from ["BOTH", "ORIGIN", "DESTINATION"]
        # selectPropertyURLList: the selected peoperty URL list, it always has three elements, "" if no property has been selected

        if len(propertyDirectionList) == 1:
            selectParam = "?p1"
        elif len(propertyDirectionList) == 2:
            selectParam = "?p2"
        elif len(propertyDirectionList) == 3:
            selectParam = "?p3"
        elif len(propertyDirectionList) == 4:
            selectParam = "?p4"

        jsonBindingObject = []
        i = 0
        while i < len(inplaceIRIList):
            if i + 50 > len(inplaceIRIList):
                inplaceIRISubList = inplaceIRIList[i:]
            else:
                inplaceIRISubList = inplaceIRIList[i:(i + 50)]
            queryPrefix = self.sparqlUTIL.make_sparql_prefix()

            # ["BOTH", "ORIGIN", "DESTINATION"]
            # if propertyDirectionList[0] == "BOTH"

            relFinderPropertyQuery = queryPrefix + """SELECT distinct """ + selectParam + """
                            WHERE {"""

            if len(propertyDirectionList) > 0:
                if selectPropertyURLList[0] == "":
                    if propertyDirectionList[0] == "BOTH":
                        relFinderPropertyQuery += """{?place ?p1 ?o1.} UNION {?o1 ?p1 ?place.}\n"""
                    elif propertyDirectionList[0] == "ORIGIN":
                        relFinderPropertyQuery += """?place ?p1 ?o1.\n"""
                    elif propertyDirectionList[0] == "DESTINATION":
                        relFinderPropertyQuery += """?o1 ?p1 ?place.\n"""

                    if relationDegree > 1:
                        relFinderPropertyQuery += """OPTIONAL {?p1 a owl:ObjectProperty.}\n"""
                else:
                    if propertyDirectionList[0] == "BOTH":
                        relFinderPropertyQuery += """{?place <""" + selectPropertyURLList[
                            0] + """> ?o1.} UNION {?o1 <""" + selectPropertyURLList[0] + """> ?place.}\n"""
                    elif propertyDirectionList[0] == "ORIGIN":
                        relFinderPropertyQuery += """?place <""" + selectPropertyURLList[0] + """> ?o1.\n"""
                    elif propertyDirectionList[0] == "DESTINATION":
                        relFinderPropertyQuery += """?o1 <""" + selectPropertyURLList[0] + """> ?place.\n"""

            if len(propertyDirectionList) > 1:
                if selectPropertyURLList[1] == "":
                    if propertyDirectionList[1] == "BOTH":
                        relFinderPropertyQuery += """{?o1 ?p2 ?o2.} UNION {?o2 ?p2 ?o1.}\n"""
                    elif propertyDirectionList[1] == "ORIGIN":
                        relFinderPropertyQuery += """?o1 ?p2 ?o2.\n"""
                    elif propertyDirectionList[1] == "DESTINATION":
                        relFinderPropertyQuery += """?o2 ?p2 ?o1.\n"""

                    if relationDegree > 2:
                        relFinderPropertyQuery += """OPTIONAL {?p2 a owl:ObjectProperty.}\n"""
                else:
                    if propertyDirectionList[1] == "BOTH":
                        relFinderPropertyQuery += """{?o1 <""" + selectPropertyURLList[1] + """> ?o2.} UNION {?o2 <""" + \
                                                  selectPropertyURLList[1] + """> ?o1.}\n"""
                    elif propertyDirectionList[1] == "ORIGIN":
                        relFinderPropertyQuery += """?o1 <""" + selectPropertyURLList[1] + """> ?o2.\n"""
                    elif propertyDirectionList[1] == "DESTINATION":
                        relFinderPropertyQuery += """?o2 <""" + selectPropertyURLList[1] + """> ?o1.\n"""

            if len(propertyDirectionList) > 2:
                if selectPropertyURLList[2] == "":
                    if propertyDirectionList[2] == "BOTH":
                        relFinderPropertyQuery += """{?o2 ?p3 ?o3.} UNION {?o3 ?p3 ?o2.}\n"""
                    elif propertyDirectionList[2] == "ORIGIN":
                        relFinderPropertyQuery += """?o2 ?p3 ?o3.\n"""
                    elif propertyDirectionList[2] == "DESTINATION":
                        relFinderPropertyQuery += """?o3 ?p3 ?o2.\n"""

                    if relationDegree > 3:
                        relFinderPropertyQuery += """OPTIONAL {?p3 a owl:ObjectProperty.}\n"""
                else:
                    if propertyDirectionList[2] == "BOTH":
                        relFinderPropertyQuery += """{?o2 <""" + selectPropertyURLList[2] + """> ?o3.} UNION {?o3 <""" + \
                                                  selectPropertyURLList[2] + """> ?o2.}\n"""
                    elif propertyDirectionList[2] == "ORIGIN":
                        relFinderPropertyQuery += """?o2 <""" + selectPropertyURLList[2] + """> ?o3.\n"""
                    elif propertyDirectionList[2] == "DESTINATION":
                        relFinderPropertyQuery += """?o3 <""" + selectPropertyURLList[2] + """> ?o2.\n"""

            if len(propertyDirectionList) > 3:
                if propertyDirectionList[3] == "BOTH":
                    relFinderPropertyQuery += """{?o3 ?p4 ?o4.} UNION {?o4 ?p4 ?o3.}\n"""
                elif propertyDirectionList[3] == "ORIGIN":
                    relFinderPropertyQuery += """?o3 ?p4 ?o4.\n"""
                elif propertyDirectionList[3] == "DESTINATION":
                    relFinderPropertyQuery += """?o4 ?p4 ?o3.\n"""

            relFinderPropertyQuery += """
                            VALUES ?place
                            {"""
            for IRI in inplaceIRISubList:
                relFinderPropertyQuery = relFinderPropertyQuery + "<" + IRI + "> \n"

            relFinderPropertyQuery = relFinderPropertyQuery + """
                            }
                            }
                            """

            res_json = self.sparqlUTIL.sparql_requests(query=relFinderPropertyQuery,
                                                  sparql_endpoint=sparql_endpoint,
                                                  doInference=False)
            jsonBindingObject.extend(res_json["results"]["bindings"])

            i = i + 50

        return jsonBindingObject


    def endPlaceInformationQuery(self, endPlaceIRIList, sparql_endpoint=None):

        if sparql_endpoint is None:
            sparql_endpoint = self.sparqlUTIL._WIKIDATA_SPARQL_ENDPOINT

        jsonBindingObject = []
        i = 0
        while i < len(endPlaceIRIList):
            if i + 50 > len(endPlaceIRIList):
                endPlaceIRISubList = endPlaceIRIList[i:]
            else:
                endPlaceIRISubList = endPlaceIRIList[i:(i + 50)]

            queryPrefix = self.sparqlUTIL.make_sparql_prefix()

            if sparql_endpoint == self.sparqlUTIL._WIKIDATA_SPARQL_ENDPOINT:
                endPlaceQuery = queryPrefix + """SELECT distinct ?place ?placeLabel ?placeFlatType ?wkt
                                WHERE {
                                ?place wdt:P625 ?wkt .
                                # retrieve the English label
                                SERVICE wikibase:label {bd:serviceParam wikibase:language "en". ?place rdfs:label ?placeLabel .}
                                ?place wdt:P31 ?placeFlatType.
                                # ?placeFlatType wdt:P279* wd:Q2221906.

                                VALUES ?place
                                {"""
            else:
                endPlaceQuery = queryPrefix + """SELECT distinct ?place ?placeLabel ?placeFlatType ?wkt
                                WHERE {
                                ?place geo:hasGeometry ?geometry .
                                ?place rdfs:label ?placeLabel .
                                ?geometry geo:asWKT ?wkt.

                                VALUES ?place
                                {"""
            for IRI in endPlaceIRISubList:
                endPlaceQuery = endPlaceQuery + "<" + IRI + "> \n"

            endPlaceQuery = endPlaceQuery + """
                            }
                            }
                            """

            res_json = self.sparqlUTIL.sparql_requests(query=endPlaceQuery,
                                                  sparql_endpoint=sparql_endpoint,
                                                  doInference=False)
            res_json = res_json["results"]["bindings"]
            jsonBindingObject.extend(res_json)

            i = i + 50

        return jsonBindingObject


    ##########
    ##
    ## Explore Plug in queries
    ##
    ##########

    def commonPropertyExploreQuery(self, feature=None, sparql_endpoint="http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire", doSameAs=True):

        queryPrefix = self.sparqlUTIL.make_sparql_prefix()

        if feature is None:
            feature="kwg-ont:SoilPolygon"

        commonPropertyQuery = queryPrefix + """
        select distinct ?p ?plabel
        where { 
            ?s ?p ?o.
            ?s rdf:type %s. 
            OPTIONAL {
                ?p rdfs:label ?plabel .
            }
        }
        """ % (feature)

        # QgsMessageLog.logMessage("commonQuery: " + commonPropertyQuery, "kwg_explore_geoenrichment", level=Qgis.Info)
        res_json = self.sparqlUTIL.sparql_requests(query=commonPropertyQuery,
                                              sparql_endpoint=sparql_endpoint,
                                              doInference=False)
        return res_json


    def commonSosaObsPropertyExploreQuery(self, feature=None, sparql_endpoint='https://dbpedia.org/sparql', doSameAs=False):
        queryPrefix = self.sparqlUTIL.make_sparql_prefix()

        if feature is None:
            feature="kwg-ont:SoilPolygon"

        commonPropertyQuery = queryPrefix + """
        select distinct ?p ?plabel
        where { 
            ?s sosa:isFeatureOfInterestOf ?obscol .
            ?obscol sosa:hasMember ?obs.
            ?obs sosa:observedProperty ?p .
            ?s rdf:type %s. 
            OPTIONAL {
                ?p rdfs:label ?plabel .
            }
        }
        """ % (feature)

        res_json = self.sparqlUTIL.sparql_requests(query=commonPropertyQuery,
                                              sparql_endpoint=sparql_endpoint,
                                              doInference=False)
        return res_json


    def inverseCommonPropertyExploreQuery(self, feature=None, sparql_endpoint='https://dbpedia.org/sparql', doSameAs=True):

        if feature is None:
            feature="kwg-ont:SoilPolygon"

        queryPrefix = self.sparqlUTIL.make_sparql_prefix()

        inversePropertyQuery = queryPrefix + """
        select
        distinct ?inverse_p ?plabel
        where
        { 
            ?s ?p ?o. 
            ?o ?inverse_p ?s. 
            ?o rdf:type %s.
            OPTIONAL
            {
                ?inverse_p rdfs:label ?plabel.
            }
        }
        """ %(feature)


        # select distinct ?inverse_p ?plabel where { ?s ?p ?o . ?o ?inverse_p ?s. ?o rdf:type " + feature + ". OPTIONAL {?inverse_p rdfs:label ?plabel .} }

        res_json = self.sparqlUTIL.sparql_requests(query=inversePropertyQuery,
                                              sparql_endpoint=sparql_endpoint,
                                              doInference=False)
        return res_json


if __name__ == "__main__":
    SQ = kwg_sparqlquery()
    # SQ.EventTypeSPARQLQuery()
    # print(SQ.sparqlUTIL.make_sparql_prefix())
