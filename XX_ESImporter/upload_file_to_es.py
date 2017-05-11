# -*- coding: utf-8 -*-

import os
import json
from elasticsearch import Elasticsearch
# by default we connect to localhost:9200


class ESUploader:
	
	def __init__(self, index_name, type_name, num_per_batch = 1000):
		self._es = Elasticsearch([{'host':'192.168.0.21','port':9200}])
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
			print "finish %d docs"%self._counter
			self._doc_buffer = []
			#print res
		else:
			self._doc_buffer.append(json.dumps({'index':{'_index': self._index,'_type':self._type}}))
			self._doc_buffer.append(json.dumps(doc))

	def commit_to_es(self):
		res = self._es.bulk("\n".join(self._doc_buffer))
		print "finish %d docs"%self._counter
		self._doc_buffer = []


class File_ESUploader(ESUploader):

	def __init__(self, index_name, type_name, data_path,  from_encoding="utf-8", to_encoding="utf-8",num_per_batch = 1000):
		ESUploader.__init__(self, index_name, type_name, num_per_batch)
		self._data_path = data_path
		self._from_encoding = from_encoding
		self._to_encoding = to_encoding

	def start_import(self):
		for filename in os.listdir(self._data_path):
			try:
				if self._from_encoding == self._to_encoding:
					ESUploader.insert_to_es(self, {"filename":filename, "content": open(self._data_path + filename,"rb").read()})
				else:
					ESUploader.insert_to_es(self, {"filename":filename, "content": open(self._data_path + filename,"rb").read().decode(self._from_encoding).encode(self._to_encoding)})
			except Exception as e:
				continue
		ESUploader.commit_to_es(self)



if __name__ == "__main__":
	uploader = File_ESUploader("nlp_company_basic_info_raw", "basic_info","./company_info_raw/", "gbk", num_per_batch = 300)
	#uploader = File_ESUploader("nlp_company_basic_info_raw", "management_info","./company_manageinfo_raw/", "gbk", num_per_batch = 300)
	#uploader = File_ESUploader("nlp_company_basic_info_raw", "basic_info",'C:\Users\pku\Documents\ipynb\Untitled Folder\stock', "gbk", num_per_batch = 300)
	
	uploader.start_import()
