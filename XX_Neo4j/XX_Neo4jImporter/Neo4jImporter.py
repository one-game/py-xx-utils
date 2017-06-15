# -*- coding: utf-8 -*-

from py2neo import Graph, Node, Relationship, NodeSelector
import json
from collections import defaultdict
import traceback
import time
from XX_Cache.XX_Cache import XXCache

######
##
# Neo4j importer ===> Import data to neo4j
##
##
######


class Neo4j_Importer:

    _use_batch_commit = False
    _create_counter = 0
    _use_cache = False

    def __init__(self, url, username, password,
                 batch_commit=False, batch_size=100):
        self._debug = False
        self._use_batch_commit = batch_commit
        self._batch_size = batch_size
        self._graph = Graph(url, username=username, password=password)
        self._cache = XXCache(limit=200)
        if self._use_batch_commit:
            self._batch_commiter = self._graph.begin()

    def set_debug(self, flag):
        self._debug = flag

    def set_cache(self, flag):
        self._use_cache = flag

    def _insert_node(self, label_name, uri, name, properties={}, remote_lookup=True):
        if self._debug:
            start_time = time.time()
        if remote_lookup:
            node = self._graph.find_one(
                label_name, property_key="uri", property_value=uri)
        else:
            node = None
        if self._debug:
            print "Neo4j find node cost %f s" % (time.time() - start_time)
        is_remote_obj = False
        if node is None:
            node = Node(label_name, uri=uri, name=name)
            for key, value in properties.iteritems():
                node[key] = value

            self._create_counter += 1
            if self._use_batch_commit:
                self._batch_commiter.create(node)
                if self._create_counter >= self._batch_size:
                    self._create_counter = 0
                    self._batch_commiter.commit()
                    self._batch_commiter = self._graph.begin()
            else:
                self._graph.create(node)
        else:  # todo: properties merging
            is_remote_obj = True
        return node

    def find_node_by_name(self, label_name, name):
        nodes = self._find_node_by_property(label_name, "name", name)
        return nodes

    def find_node_by_uri(self, label_name, name):
        nodes = self._find_node_by_property(label_name, "uri", name)
        nodes = [n for n in nodes]
        if len(nodes) == 0:
            return None
        else:
            return nodes[0]

    def _find_node_by_property(self, label_name, property_key, property_value):
        nodes = self._graph.find(
            label_name, property_key=property_key,
            property_value=property_value)
        return nodes

    def _insert_relation(self, source_node,
                         target_node, relation_name, properties={}):
        # self._graph.match_one(source_node, relation_name, target_node)
        rel = None
        if rel is None:
            rel = Relationship(source_node, relation_name, target_node)
            for key, value in properties.iteritems():
                rel[key] = value

            self._create_counter += 1
            if self._use_batch_commit:
                self._batch_commiter.create(rel)
                if self._create_counter >= self._batch_size:
                    self._create_counter = 0
                    self._batch_commiter.commit()
                    self._batch_commiter = self._graph.begin()
            else:
                self._graph.create(rel)
        else:  # todo: if exist do something
            pass
        return rel

    ###
    # entity_info = { "label": "xxxxx"
    # "uri":"xxx",
    # "name":"xxxx",
    # "properties":{...},
    # "relations":[
    ##  {"name":"relationname","target_node":{"label":"yy","uri":"yy","name":"yy", "properties":{}},"properties":{} }
    # ]
    # }
    ##
    ##
    def insert_to_graph(self, entity_info, source_remote_lookup=True, target_remote_lookup=True):
        source_node = None
        if self._use_cache:
            source_node = self._cache.get(entity_info['uri'])
        if source_node is None:
            if "existed" in entity_info and entity_info["existed"]:
                source_node = self.find_node_by_uri(
                    entity_info["label"], entity_info["uri"])
                if source_node is None:
                    return False
            source_node = self._insert_node(entity_info["label"],
                                            entity_info["uri"],
                                            entity_info["name"],
                                            entity_info["properties"],
                                            source_remote_lookup)
            if self._use_cache:
                self._cache.add(entity_info["uri"], source_node)
        for relation_info in entity_info["relations"]:
            relation_name = relation_info["name"]
            properties = relation_info["properties"]
            for target_info in relation_info["target_nodes"]:
                target_node = None
                if self._use_cache:
                    target_node = self._cache.get(target_info['uri'])
                if target_node is None:
                    if self._debug:
                        start_time = time.time()
                    if "existed" in target_info and target_info["existed"]:
                        target_node = self.find_node_by_uri(
                            target_info["label"], target_info["uri"])
                        if target_node is None:
                            return False
                    target_node = self._insert_node(target_info["label"],
                                                    target_info["uri"],
                                                    target_info["name"],
                                                    target_info["properties"],
                                                    target_remote_lookup)
                    if self._debug:
                        print "insert relation cost %f s" % (time.time() - start_time)
                    if self._use_cache:
                        self._cache.add(target_info['uri'], target_node)
                if self._debug:
                    start_time = time.time()
                self._insert_relation(
                    source_node, target_node, relation_name, properties)
                if self._debug:
                    print "insert relation cost %f s" % (time.time() - start_time)
        return True
