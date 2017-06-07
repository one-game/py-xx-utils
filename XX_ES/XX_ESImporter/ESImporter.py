# -*- coding: utf-8 -*-

import os
import json
from elasticsearch import Elasticsearch
import traceback
# by default we connect to localhost:9200


class ESImporter:

    def __init__(self, es_server_list,index_name, type_name="doc", num_per_batch=1000):
        self._es = Elasticsearch(es_server_list)
        self._doc_buffer = []
        self._counter = 0
        self._index = index_name
        self._type = type_name
        self._num_per_batch = num_per_batch

    def insert_to_es(self, doc):
        self._counter += 1
        if len(self._doc_buffer) >= self._num_per_batch:
            while True:
                try:
                    res = self._es.bulk("\n".join(self._doc_buffer))
                    break
                except Exception as e:
                    print "bulk failed"
                    continue
            print "finish %d docs" % self._counter
            self._doc_buffer = []
            # print res
        else:
            self._doc_buffer.append(json.dumps(
                {'index': {'_index': self._index, '_type': self._type}}))
            self._doc_buffer.append(json.dumps(doc))

    def commit_to_es(self):
        res = self._es.bulk("\n".join(self._doc_buffer))
        print "finish %d docs" % self._counter
        self._doc_buffer = []


class Echo_ESImporter(ESImporter):
    def __init__(self):
        pass

    def insert_to_es(self, doc):
        print doc
        pass

    def commit_to_es(self):
        pass
