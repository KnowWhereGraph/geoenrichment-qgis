import requests


class kwg_sparqlutil:
    # NAME_SPACE = "http://stko-roy.geog.ucsb.edu/"
    NAME_SPACE = "http://stko-kwg.geog.ucsb.edu/"

    # _SPARQL_ENDPOINT = "http://stko-roy.geog.ucsb.edu:7200/repositories/kwg-seed-graph-v2"
    _SPARQL_ENDPOINT = "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire"
    _WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

    _PREFIX = {
        "kwgr": f"{NAME_SPACE}lod/resource/",
        "kwg-ont": f"{NAME_SPACE}lod/ontology/",
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


    @staticmethod
    def make_sparql_prefix():
        """
        Generates sparql prefix string
        """
        query_prefix = ''
        for prefix in kwg_sparqlutil._PREFIX:
            query_prefix += f"PREFIX {prefix}: <{kwg_sparqlutil._PREFIX[prefix]}>\n"
        return query_prefix

    @staticmethod
    def make_prefixed_iri(iri):
        """

        """
        prefixed_iri = ""
        for prefix in kwg_sparqlutil._PREFIX:
            if kwg_sparqlutil._PREFIX[prefix] in iri:
                prefixed_iri = iri.replace(kwg_sparqlutil._PREFIX[prefix], prefix + ":")
                break
        if prefixed_iri == "":
            return iri
        else:
            return prefixed_iri

    @staticmethod
    def make_prefixed_iri_batch(iri_list):
        """

        """
        prefixed_iri_list = []
        for iri in iri_list:
            prefixed_iri = kwg_sparqlutil.make_prefixed_iri(iri)
            prefixed_iri_list.append(prefixed_iri)
        return prefixed_iri_list

    @staticmethod
    def sparql_requests(query, sparql_endpoint, doInference=False, request_method='post'):
        """

        """
        # sparqlParam = {'query':'SELECT ?item ?itemLabel WHERE{ ?item wdt:P31 wd:Q146 . SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }}', 'format':'json'}
        print(query)
        sparqlParam = {'query': query, 'format': 'json', 'infer': "true" if doInference else "false"}
        headers = {'Accept': 'application/sparql-results+json'}
        # headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        if request_method == 'post':
            sparqlRequest = requests.post(sparql_endpoint, data=sparqlParam, headers=headers)
        elif request_method == 'get':
            sparqlRequest = requests.get(sparql_endpoint, params=sparqlParam, headers=headers)
        else:
            raise Exception(f"request method {request_method} noy find")
        print(sparqlRequest.url)

        entityTypeJson = sparqlRequest.json()  # ["results"]["bindings"]
        return entityTypeJson
