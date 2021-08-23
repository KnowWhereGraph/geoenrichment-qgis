import json
import logging

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

        GeoQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                    sparql_endpoint=sparql_endpoint,
                                                    doInference=False,
                                                    request_method="get")
        GeoQueryResult = GeoQueryResult["results"]["bindings"]
        print(json.dumps(GeoQueryResult, indent=2))
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

        # query = queryPrefix + """
        #         select distinct ?place ?placeLabel ?placeFlatType ?wkt
        #         where
        #         {

        #             ?place geo:hasGeometry ?geometry .
        #             ?place rdfs:label ?placeLabel .
        #             ?geometry geo:asWKT ?wkt.
        #             FILTER (""" + geosparql_func[0] + """('''
        #         <http://www.opengis.net/def/crs/OGC/1.3/CRS84>
        #         """ + query_geo_wkt + """
        #         '''^^geo:wktLiteral, ?wkt)
        #     """
        # if len(geosparql_func) == 1:
        #     query += ")"
        # elif len(geosparql_func) == 2:
        #     query += """ ||
        #         """ + geosparql_func[1] + """('''
        #         <http://www.opengis.net/def/crs/OGC/1.3/CRS84>
        #         """ + query_geo_wkt + """
        #         '''^^geo:wktLiteral, ?wkt)
        #         )
        #     """
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
        # if len(geosparql_func) == 1:
        #     query += ")"
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
        queryPrefix = self.SPARQLUtil.make_sparql_prefix()

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
                propertyName = f"""{label} [{jsonItem[numofsub_var]["value"]}]"""
                p_name_list.append(propertyName)

        url_dict = dict(zip(p_name_list, p_url_list))

        return url_dict
    

if __name__ == "__main__":
    SQ = kwg_sparqlquery()
    SQ.EventTypeSPARQLQuery()


