import json
import logging
import os

import requests


class kwg_sparqlutil:

    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.path = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

        if not os.path.exists(os.path.join(self.path, 'logs')):
            os.makedirs(os.path.join(self.path, 'logs'))
        handler = logging.FileHandler(os.path.join(self.path, 'logs', 'kwg_geoenrichment.log'), 'w+', 'utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
        handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
        self.logger.addHandler(handler)

    NAME_SPACE = "http://stko-kwg.geog.ucsb.edu"

    _SPARQL_ENDPOINT = "https://stko-roy.geog.ucsb.edu/graphdb/repositories/KWG"
    _WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

    _PREFIX = {
        "kwg-ont": "http://stko-kwg.geog.ucsb.edu/lod/ontology/",
        "kwgr": "http://stko-kwg.geog.ucsb.edu/lod/resource/",
        "geo": "http://www.opengis.net/ont/geosparql#",
        "geof": "http://www.opengis.net/def/function/geosparql/",
        "gnisf": "http://gnis-ld.org/lod/gnis/feature/",
        "cegis": "http://gnis-ld.org/lod/cegis/ontology/",
        "sosa": "http://www.w3.org/ns/sosa/",
        "ago": "http://awesemantic-geo.link/ontology/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "time": "http://www.w3.org/2006/time#",
        "xvd": "http://www.w3.org/2001/XMLSchema#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "iospress": "http://ld.iospress.nl/rdf/ontology/"
    }

    _SPARQL_ENDPOINT_DICT = {
        "prod": {
            "kwg-v2": "http://stko-kwg.geog.ucsb.edu:7200/repositories/KWG"
        },
        "test": {
            "plume_soil_wildfire": "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire",

        }
    }

    def make_sparql_prefix(self):
        """
        Generates sparql prefix string
        """
        query_prefix = ''
        for prefix in self._PREFIX:
            query_prefix += f"PREFIX {prefix}: <{self._PREFIX[prefix]}>\n"
        return query_prefix

    def make_prefixed_iri(self, iri):
        """

        """
        prefixed_iri = ""
        for prefix in self._PREFIX:
            if self._PREFIX[prefix] in iri:
                prefixed_iri = iri.replace(self._PREFIX[prefix], prefix + ":")
                break
        if prefixed_iri == "":
            return iri
        else:
            return prefixed_iri

    def remake_prefixed_iri(self, prefixed_iri):
        """

        """
        striped_iri = prefixed_iri.split(":")
        iri = prefixed_iri

        if striped_iri[0] in self._PREFIX:
            self.logger.info(striped_iri[0])
            self.logger.info(striped_iri[1])
            iri = self._PREFIX[striped_iri[0]] + striped_iri[1]

        return iri

    def make_prefixed_iri_batch(self, iri_list):
        """

        """
        prefixed_iri_list = []
        for iri in iri_list:
            prefixed_iri = self.make_prefixed_iri(iri)
            prefixed_iri_list.append(prefixed_iri)
        return prefixed_iri_list

    def sparql_requests(self, query, sparql_endpoint, doInference=False, request_method='post'):
        """

        """

        entityTypeJson = {
            "results": {
                "bindings": {}
            }
        }

        self.logger.debug("query: ")
        self.logger.debug(query)

        if sparql_endpoint is None:
            url = self.SPARQL_ENDPOINT
        else:
            url = sparql_endpoint

        sparqlParam = {'query': query, 'format': 'json'}
        headers = {'Accept': 'application/sparql-results+json'}

        try:
            if request_method == 'post':
                sparqlRequest = requests.post(url=url, data=sparqlParam, headers=headers)
                # self.logger.debug(url)
                # self.logger.debug(json.dumps(sparqlParam))
                if sparqlRequest.status_code == 200:
                    entityTypeJson = sparqlRequest.json()  # ["results"]["bindings"]
                    self.logger.debug("HTTP request OK")
                    # self.logger.debug(sparqlRequest.text)
                else:
                    self.logger.debug("!200")
                    self.logger.debug(sparqlRequest.text)
            elif request_method == 'get':
                sparqlRequest = requests.get(url=url, params=sparqlParam, headers=headers)
                # self.logger.debug(url)
                # self.logger.debug(json.dumps(sparqlParam))
                if sparqlRequest.status_code == 200:
                    entityTypeJson = sparqlRequest.json()  # ["results"]["bindings"]
                    self.logger.debug("HTTP request OK")
                    # self.logger.debug(sparqlRequest.text)
                else:
                    self.logger.debug("!200")
                    self.logger.debug(sparqlRequest.text)
            else:
                raise Exception(f"request method {request_method} not found")

        except Exception as e:
            self.logger.exception(e)

        return entityTypeJson


if __name__ == '__main__':
    SU = kwg_sparqlutil()
    print(SU.make_sparql_prefix())
