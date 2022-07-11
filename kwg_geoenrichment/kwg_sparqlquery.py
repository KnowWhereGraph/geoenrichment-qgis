import json
import logging
import os
from collections import namedtuple
from qgis.core import QgsMessageLog, Qgis

from .kwg_sparqlutil import kwg_sparqlutil


class kwg_sparqlquery:

    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  
        self.sparqlUTIL = kwg_sparqlutil()
        self.path = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

        if not os.path.exists(os.path.join(self.path, 'logs')):
            os.makedirs(os.path.join(self.path, 'logs'))
        handler = logging.FileHandler(os.path.join(self.path, 'logs', 'kwg_geoenrichment.log'), 'w+', 'utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
        handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
        self.logger.addHandler(handler)

    def getS2CellsFromGeometry(self,
                               sparql_endpoint="http://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
                               wkt_literal="Polygon((-119.73822343857 34.4749685817967, -119.571162553598 34.4767458252538, -119.670688187198 34.3754429481962, -119.73822343857 34.4749685817967))"):
        """
            Retrieves S2 cells based on the selected wkt literal
            Arguments:
                sparql_endpoint: the sparql end point for the graph database
                wkt_literal: the wkt literal for the user selected polygon
            Returns:
                The raw JSON response containing S2 cells retrieved from the specified graph end point
        """

        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        queryString = """
        select ?s2Cell where {
            ?adminRegion2 a kwg-ont:AdministrativeRegion_3.
            ?adminRegion2 geo:hasGeometry ?arGeo.
            ?arGeo geo:asWKT ?arWKT.
            FILTER(geof:sfIntersects("%s"^^geo:wktLiteral, ?arWKT) || geof:sfWithin("%s"^^geo:wktLiteral, ?arWKT)).

            ?adminRegion2 kwg-ont:sfContains ?s2Cell.
            ?s2Cell a kwg-ont:KWGCellLevel13.
            ?s2Cell geo:hasGeometry ?s2Geo.
            ?s2Geo geo:asWKT ?s2WKT.
            FILTER(geof:sfIntersects("%s"^^geo:wktLiteral, ?s2WKT) || geof:sfWithin("%s"^^geo:wktLiteral, ?s2WKT)).
        }
        """ % (wkt_literal, wkt_literal, wkt_literal, wkt_literal)

        query = queryPrefix + queryString

        try:

            s2CellsQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                        sparql_endpoint=sparql_endpoint,
                                                        request_method="get")

            if s2CellsQueryResult is None:
                return "error: s2c"

            s2CellsQueryResultBindings = s2CellsQueryResult["results"]["bindings"]

        except:
            return "error: s2c"

        return s2CellsQueryResultBindings

    def getEntityValuesFromS2Cells(self,
                                   sparql_endpoint="http://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
                                   s2Cells=[]):
        """
            Retrieves Entity values that are associated with the passed S2 cells
            Arguments:
                sparql_endpoint: the sparql end point for the graph database
                s2Cells: list object of the S2 cells that belong to the user selected polygon
            Returns:
                The raw JSON response containing Entity values
        """

        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        EntityQueryResultBindings = []

        try:
            s2CellsPrefixed = ""
            for s2Cell in s2Cells:
                s2CellsPrefixed += " " + self.sparqlUTIL.make_prefixed_iri(s2Cell)

            queryString = """
            select distinct ?entity where {
                {?entity ?p ?s2Cell.} union {?s2Cell ?p ?entity.}
                ?entity a geo:Feature.
                values ?s2Cell {%s}
            }
            """ % (s2CellsPrefixed)

            query = queryPrefix + queryString

            EntityQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                           sparql_endpoint=sparql_endpoint,
                                                           doInference=False,
                                                           request_method="post")
            EntityQueryResultBindings.extend(EntityQueryResult["results"]["bindings"])

        except:
            return "error: ent"

        return EntityQueryResultBindings

    def getFirstDegreeClass(self,
                            sparql_endpoint="http://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
                            entityList=[]
                            ):
        """
            Retrieves first degree class given the entity list
            Arguments:
                sparql_endpoint: the sparql end point for the graph database
                entityList: list object of entities associated with the S2Cells
            Returns:
                The raw JSON response containing first degree class
        """

        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        FirstDegreeClassQueryResultBindings = []

        try:

            entityPrefixed = ""
            for entity in entityList:
                entityPrefixed += " " + self.sparqlUTIL.make_prefixed_iri(entity)

            queryString = """
                    select distinct ?type ?label where {
                        ?entity a ?type.
                        ?type rdfs:label ?label.
                        values ?entity {%s}
                    }
                    """ % (entityPrefixed)
            # self.logger.debug("Class0Debug: " + queryString)

            query = queryPrefix + queryString

            FirstDegreeClassQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                                     sparql_endpoint=sparql_endpoint,
                                                                     doInference=False,
                                                                     request_method="post")
            FirstDegreeClassQueryResultBindings.extend(FirstDegreeClassQueryResult["results"]["bindings"])

        except:
            return "error: sub0"
        return FirstDegreeClassQueryResultBindings

    def getFirstDegreePredicate(self,
                                sparql_endpoint="http://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
                                entityList=[],
                                firstDegreeClass=""
                                ):
        """
            Retrieves first degree predicate given first degree class and entity list
            Arguments:
                sparql_endpoint: the sparql end point for the graph database
                entityList: list object of entities associated with the S2Cells
                firstDegreeClass: the name of the user selected first degree class
            Returns:
                The raw JSON response containing first degree predicate
        """

        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        FirstDegreePredicateQueryResultBindings = []

        try:

            entityPrefixed = ""
            for entity in entityList:
                entityPrefixed += " " + self.sparqlUTIL.make_prefixed_iri(entity)

            queryString = """
                    select distinct ?p ?label where {
                        ?entity a %s;
                            ?p ?o.
                        optional {?p rdfs:label ?label}
                        values ?entity {%s}
                    }
                    """ % (firstDegreeClass, entityPrefixed)

            query = queryPrefix + queryString

            FirstDegreePredicateQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                                         sparql_endpoint=sparql_endpoint,
                                                                         doInference=False,
                                                                         request_method="post")
            FirstDegreePredicateQueryResultBindings.extend(FirstDegreePredicateQueryResult["results"]["bindings"])

        except:
            return  "error: pred0"

        return FirstDegreePredicateQueryResultBindings

    def getFirstDegreeObject(self,
                             sparql_endpoint="http://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
                             entityList=[],
                             firstDegreeClass="",
                             firstDegreePredicate=""
                             ):
        """
            Retrieves first degree object given first degree class, first degree predicate and entity list
            Arguments:
                sparql_endpoint: the sparql end point for the graph database
                entityList: list object of entities associated with the S2Cells
                firstDegreeClass: the name of the user selected first degree class
                firstDegreePredicate: the name of the user selected first degree predicate
            Returns:
                The raw JSON response containing first degree object
        """

        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        FirstDegreeObjectQueryResultBindings = []

        try:

            entityPrefixed = ""
            for entity in entityList:
                entityPrefixed += " " + self.sparqlUTIL.make_prefixed_iri(entity)

            queryString = """
                    select distinct ?type ?label ?o where {
                        ?entity a %s; %s ?o.
                        ?o a ?type. ?type rdfs:label ?label.
                        values ?entity {%s}
                    }
                    """ % (firstDegreeClass, firstDegreePredicate, entityPrefixed)

            query = queryPrefix + queryString

            FirstDegreeObjectQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                                      sparql_endpoint=sparql_endpoint,
                                                                      doInference=False,
                                                                      request_method="post")
            FirstDegreeObjectQueryResultBindings.extend(FirstDegreeObjectQueryResult["results"]["bindings"])
        except:
            return "error: obj0"
        return FirstDegreeObjectQueryResultBindings

    def getNDegreePredicate(self,
                                sparql_endpoint="http://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
                                entityList=[],
                                selectedVals=[],
                                degree=0
                                ):
        """
            Retrieves first degree predicate given first degree class and entity list
            Arguments:
                sparql_endpoint: the sparql end point for the graph database
                entityList: list object of entities associated with the S2Cells
                firstDegreeClass: the name of the user selected first degree class
            Returns:
                The raw JSON response containing first degree predicate
        """

        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        FirstNPredicateQueryResultBindings = []

        try:

            entityPrefixed = ""
            for entity in entityList:
                entityPrefixed += " " + self.sparqlUTIL.make_prefixed_iri(entity)

            propQuery = "select distinct ?p ?label where { \n";

            for i in range(1, degree+1):
                subjectStr = "?entity" if (i == 1)  else "?o" + str(i - 1)
                classStr = selectedVals[2 * (i-1)]
                predicateStr = "?p" if (i == degree) else selectedVals[2 * (i-1) + 1]
                objectStr = "?o" + str(i)

                propQuery += subjectStr + " a " + classStr + "; " + predicateStr + " " + objectStr + ". "

            propQuery += "optional {?p rdfs:label ?label} values ?entity { %s } }" % (entityPrefixed)

            query = queryPrefix + propQuery
            self.logger.debug(query)

            FirstDegreePredicateQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                                         sparql_endpoint=sparql_endpoint,
                                                                         doInference=False,
                                                                         request_method="post")
            FirstNPredicateQueryResultBindings.extend(FirstDegreePredicateQueryResult["results"]["bindings"])

        except:
            return "error: predN"

        return FirstNPredicateQueryResultBindings

    def getNDegreeObject(self,
                             sparql_endpoint="http://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
                             entityList=[],
                             selectedVals=[],
                             degree=0
                             ):
        """
            Retrieves first degree object given first degree class, first degree predicate and entity list
            Arguments:
                sparql_endpoint: the sparql end point for the graph database
                entityList: list object of entities associated with the S2Cells
                firstDegreeClass: the name of the user selected first degree class
                firstDegreePredicate: the name of the user selected first degree predicate
            Returns:
                The raw JSON response containing first degree object
        """

        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        NDegreeObjectQueryResultBindings = []

        try:

            entityPrefixed = ""
            for entity in entityList:
                entityPrefixed += " " + self.sparqlUTIL.make_prefixed_iri(entity)

            objQuery = "select distinct ?type ?label where {  \n";

            for i in range(1, degree + 1):
                subjectStr = "?entity" if (i == 1) else "?o" + str(i - 1)
                classStr = selectedVals[2 * (i - 1)]
                predicateStr = selectedVals[2 * (i - 1) + 1]
                objectStr = "?o. ?o a ?type" if (i == degree) else "?o" + str(i)

                objQuery += subjectStr + " a " + classStr + "; " + predicateStr + " " + objectStr + ". "

            objQuery += "?type rdfs:label ?label. values ?entity { %s } }" % (entityPrefixed)

            query = queryPrefix + objQuery

            self.logger.debug(query)

            NDegreeObjectQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                                      sparql_endpoint=sparql_endpoint,
                                                                      doInference=False,
                                                                      request_method="post")
            NDegreeObjectQueryResultBindings.extend(NDegreeObjectQueryResult["results"]["bindings"])
        except:
            return "error: objN"
        return NDegreeObjectQueryResultBindings

    def getNDegreeResults(self,
                          sparql_endpoint="http://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
                          entityList=[],
                          selectedVals=[],
                          degree=0
                          ):
        """

        """
        SPARQLUtil = kwg_sparqlutil()
        queryPrefix = SPARQLUtil.make_sparql_prefix()

        NDegreeResultBindings = []

        try:
            entityPrefixed = ""
            for entity in entityList:
                entityPrefixed += " " + self.sparqlUTIL.make_prefixed_iri(entity)

            finalObject = "?o" + str(degree)

            # content 2
            sub_query = "select distinct ?entity ?entityLabel ?o %s ?wkt where { ?entity rdfs:label ?entityLabel. " % (finalObject)
            for i in range (0, len(selectedVals)):
                if i % 2 == 0:
                    if i == 0:
                        entityName = "?entity";
                    else:
                        entityName =  "?o" if (i + 1 == len(selectedVals)) else "?o" + str(i//2)
                    className = selectedVals[i]
                    sub_query += entityName + " a " + className + ". "
                else:
                    if i == 1:
                        entityName = "?entity"
                        nextEntityName = "?o" if (i + 1 == len(selectedVals)) else "?o1"
                    else:
                        entityName = "?o" + str(i//2)
                        nextEntityName = "?o" if (i + 1 == len(selectedVals)) else "?o" + str (i//2 + 1)
                    propName = selectedVals[i]
                    sub_query += entityName + " " + propName + " " + nextEntityName + ". "
            sub_query += "\t\t\t optional {?entity geo:hasGeometry ?geo. ?geo geo:asWKT ?wkt} values ?entity {%s}}" % (
                entityPrefixed)

            query = queryPrefix + sub_query
            self.logger.info("programmed: " + query)

            self.logger.debug(query)

            NDegreeObjectQueryResult = SPARQLUtil.sparql_requests(query=query,
                                                                  sparql_endpoint=sparql_endpoint,
                                                                  doInference=False,
                                                                  request_method="post")
            for obj in NDegreeObjectQueryResult["results"]["bindings"]:
                NDegreeResultBindings.append(obj)
        except:
            return "error: res"
        return NDegreeResultBindings

if __name__ == "__main__":
    SQ = kwg_sparqlquery()
    # SQ.EventTypeSPARQLQuery()
    # print(SQ.sparqlUTIL.make_sparql_prefix())
    print(SQ.getS2CellsFromGeometry())
