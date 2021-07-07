import json

from kwg_sparqlutil import kwg_sparqlutil



class kwg_sparqlquery:

    def EventTypeSPARQLQuery( sparql_endpoint="http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"):
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


if __name__ == "__main__":
    SQ = kwg_sparqlquery()
    SQ.EventTypeSPARQLQuery()


