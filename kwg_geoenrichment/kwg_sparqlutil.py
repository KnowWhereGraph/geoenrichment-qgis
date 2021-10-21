import logging

import requests


class kwg_sparqlutil:

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



    # NAME_SPACE = "http://stko-roy.geog.ucsb.edu"
    NAME_SPACE = "http://stko-kwg.geog.ucsb.edu"

    # _SPARQL_ENDPOINT = "http://stko-roy.geog.ucsb.edu:7200/repositories/kwg-seed-graph-v2"
    _SPARQL_ENDPOINT = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"
    _WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

    _PREFIX = {
        "kwgr": "%s/lod/resource/" %  (NAME_SPACE),
        "kwg-ont": "%s/lod/ontology/" %  (NAME_SPACE),
        "geo": "http://www.opengis.net/ont/geosparql#",
        "geof": "http://www.opengis.net/def/function/geosparql/",
        "wd": "http://www.wikidata.org/entity/",
        "wdt": "http://www.wikidata.org/prop/direct/",
        "wikibase": "http://wikiba.se/ontology#",
        "bd": "http://www.bigdata.com/rdf#",
        "rdf": 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        "rdfs": 'http://www.w3.org/2000/01/rdf-schema#',
        "xsd": 'http://www.w3.org/2001/XMLSchema#',
        "owl": "http://www.w3.org/2002/07/owl#",
        "time": 'http://www.w3.org/2006/time#',
        "dbo": "http://dbpedia.org/ontology/",
        "dbr": "http://dbpedia.org/resource/",
        "time": "http://www.w3.org/2006/time#",
        "ssn": "http://www.w3.org/ns/ssn/",
        "sosa": "http://www.w3.org/ns/sosa/",
        "geo-pos": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "omgeo": "http://www.ontotext.com/owlim/geo#",
        "ff": "http://factforge.net/",
        "om": "http://www.ontotext.com/owlim/",
        "schema": "http://schema.org/",
        "p": "http://www.wikidata.org/prop/",
        "wdtn": "http://www.wikidata.org/prop/direct-normalized/"
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
        # sparqlParam = {'query':'SELECT ?item ?itemLabel WHERE{ ?item wdt:P31 wd:Q146 . SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }}', 'format':'json'}

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

        sparqlParam = {'query': query, 'format': 'json', 'infer': "true" if doInference else "false"}
        headers = {'Accept': 'application/sparql-results+json'}
        # headers = {'Content-type': 'application/json', 'Accept': 'application/sparql-results+json'}

        try:
            if request_method == 'post':
                sparqlRequest = requests.post(url=url, data=sparqlParam, headers=headers)
                if sparqlRequest.status_code == 200:
                    entityTypeJson = sparqlRequest.json()  # ["results"]["bindings"]
                    self.logger.debug("HTTP request OK")
                else:
                    self.logger.debug("!200")
                    self.logger.debug(sparqlRequest.text)
            elif request_method == 'get':
                sparqlRequest = requests.get(url=url, params=sparqlParam, headers=headers)
                if sparqlRequest.status_code == 200:
                    entityTypeJson = sparqlRequest.json()  # ["results"]["bindings"]
                    self.logger.debug("HTTP request OK")
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