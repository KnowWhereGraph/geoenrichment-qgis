import json
import logging

from .kwg_sparqlutil import kwg_sparqlutil

class kwg_sparqlquery:

    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # or whatever
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


if __name__ == "__main__":
    SQ = kwg_sparqlquery()
    SQ.EventTypeSPARQLQuery()


