# -*- coding: utf-8 -*-


from elasticsearch import Elasticsearch
import time

class ESExporter():

    _debug = False

    def __init__(self, es_server_list,
                 index_name,
                 type_name="doc",
                 query={},
                 timeout=6000,
                 batch_size=100):
        if not isinstance(es_server_list, list):
            # throw exception
            return False
        self._es = Elasticsearch(es_server_list)
        self._index_name = index_name
        self._type_name = type_name
        self._es_query = query
        self._es_query['size'] = batch_size
        self._timeout = timeout
        self._batch_size = batch_size

    def set_debug(self, flag):
        self._debug = flag

    def fetch_data(self, scroll_id=None, size=100):
        if scroll_id is None:
            # print self._es_query, self._index_name, self._type_name
            if self._debug:
                start_time = time.time()
            res = self._es.search(index=self._index_name,
                                  doc_type=self._type_name,
                                  request_timeout=self._timeout,
                                  body=self._es_query,
                                  scroll='10m')
            if self._debug:
                print "es_query cost %fs" % (time.time() - start_time)
            # print res
        else:
            if self._debug:
                start_time = time.time()
            res = self._es.scroll(scroll_id=scroll_id, scroll="10m")
            if self._debug:
                print "es_query cost %fs" % (time.time() - start_time)
        scroll_id = res["_scroll_id"]
        if len(res['hits']['hits']) == 0:
            # print "return record list is empty"
            return
        # print len(res['hits']['hits'])
        for record in res['hits']['hits']:
            yield record["_source"]
        for record in self.fetch_data(scroll_id):
            yield record

    def get_total_count(self):
        res = self._es.search(index=self._index_name,
                              doc_type=self._type_name,
                              body=self._es_query)
        if "hits" in res and "total" in res["hits"]:
            return res["hits"]["total"]
        else:
            return -1
