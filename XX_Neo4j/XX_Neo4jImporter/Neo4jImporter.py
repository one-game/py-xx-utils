# -*- coding: utf-8 -*-

from py2neo import Graph, Node, Relationship, NodeSelector
import json
from collections import defaultdict
import traceback


######
##
# Neo4j importer ===> Import data to neo4j
##
##
######
class Neo4j_Importer:

    def __init__(self, url, username, password):
        self._debug = False
        self._graph = Graph(url, username=username, password=password)

    def set_debug(self, flag):
        self._debug = flag

    def _insert_node(self, label_name, uri, name, properties={}):
        node = self._graph.find_one(
            label_name, property_key="uri", property_value=uri)
        is_remote_obj = False
        if node is None:
            node = Node(label_name, uri=uri, name=name)
            for key, value in properties.iteritems():
                node[key] = value
            self._graph.create(node)
        else:  # todo: properties merging
            is_remote_obj = True
        return node

    def find_node_by_name(self, label_name, name):
        nodes = self._graph.find(
            label_name, property_key="name", property_value=name)
        return nodes

    def _insert_relation(self, source_node,
                         target_node, relation_name, properties={}):
        rel = self._graph.match_one(source_node, relation_name, target_node)
        if rel is None:
            rel = Relationship(source_node, relation_name, target_node)
            for key, value in properties.iteritems():
                rel[key] = value
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
    ##	{"name":"relationname","target_node":{"label":"yy","uri":"yy","name":"yy", "properties":{}},"properties":{} }
    # ]
    # }
    ##
    ##
    def insert_to_graph(self, entity_info):
        source_node = self._insert_node(entity_info["label"],
                                        entity_info["uri"],
                                        entity_info["name"],
                                        entity_info["properties"])
        for relation_info in entity_info["relations"]:
            relation_name = relation_info["name"]
            properties = relation_info["properties"]
            for target_info in relation_info["target_nodes"]:
                target_node = self._insert_node(target_info["label"],
                                                target_info["uri"],
                                                target_info["name"],
                                                target_info["properties"])
                self._insert_relation(
                    source_node, target_node, relation_name, properties)
