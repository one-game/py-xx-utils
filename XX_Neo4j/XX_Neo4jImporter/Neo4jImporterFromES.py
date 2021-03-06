# -*- coding: utf-8 -*-

from tqdm import tqdm
from Neo4jImporter import Neo4j_Importer
import time

######
##
# derived class of neo4j_importer ===> import data to neo4j from es
##
##
##
#######


class Neo4j_Importer_From_ES(Neo4j_Importer):

    _show_progress = False

    def __init__(self, es_exporter, url, username, password, batch_size=0):
        if batch_size == 0:
            Neo4j_Importer.__init__(self, url, username, password)
        else:
            Neo4j_Importer.__init__(
                self, url, username, password, True, batch_size)
        self._exporter = es_exporter

    ########
    #
    # transform data between es and neo4j
    #
    ##########
    def _transform_to_entity(self, es_data):
        entity_info = {}
        yield entity_info

    def set_show_progress(self, flag):
        self._show_progress = flag

    def process(self):
        total_count = self._exporter.get_total_count()
        # if self._debug:
        #     print "=====before fetch data======="
        if self._show_progress:
            iter_list = tqdm(self._exporter.fetch_data(), total=total_count)
        else:
            iter_list = self._exporter.fetch_data()
        for data in iter_list:
            # if self._debug:
            #     print "========data========="
            #     print data
            #     print "========end of data======="
            if self._debug:
                start_time = time.time()
            for trans_data in self._transform_to_entity(data):
                if trans_data is not None:
                    if self._debug:
                        start_time_1 = time.time()
                    if not Neo4j_Importer.insert_to_graph(self, trans_data):
                        if self._debug:
                            print trans_data
                    if self._debug:
                        print "insert to graph cost %f s" % (time.time() - start_time_1)
            if self._debug:
                print "transform data cost %f s" % (time.time() - start_time)
            # break
