# -*- coding: utf-8 -*-

import os
import json
from elasticsearch import Elasticsearch
from ESUploader import ESUploader
import traceback
# by default we connect to localhost:9200


class File_ESUploader(ESUploader):

    def __init__(self, index_name, type_name, data_path,
                 from_encoding="utf-8", to_encoding="utf-8",
                 num_per_batch=1000):
        ESUploader.__init__(self, index_name, type_name, num_per_batch)
        self._data_path = data_path
        self._from_encoding = from_encoding
        self._to_encoding = to_encoding

    def start_import(self, filename_prefix=""):
        for filename in os.listdir(self._data_path):
            try:
                if self._from_encoding == self._to_encoding:
                    ESUploader.insert_to_es(self,
                                            {
                                                "filename": filename_prefix + filename,
                                                "content": open(self._data_path + filename, "rb").read()
                                            }
                                            )
                else:
                    ESUploader.insert_to_es(self, {"filename": filename_prefix + filename, "content": open(
                        self._data_path + filename, "rb").read().decode(self._from_encoding).encode(self._to_encoding)})
            except Exception as e:
                traceback.print_exc()
                break
                continue
        ESUploader.commit_to_es(self)


if __name__ == "__main__":
    uploader = File_ESUploader("company_notice_raw_data_v1", "raw_doc", unicode(
        "D:\\work\\pku\\语义搜索引擎\\新浪财经抓取\\notice.sample\\notices\\601788\\", "utf-8"), "utf-8", num_per_batch=300)
    #uploader = File_ESUploader("nlp_company_basic_info_raw", "management_info","./company_manageinfo_raw/", "gbk", num_per_batch = 300)
    # uploader = File_ESUploader("nlp_company_basic_info_raw",
    # "basic_info",'C:\Users\pku\Documents\ipynb\Untitled Folder\stock',
    # "gbk", num_per_batch = 300)

    uploader.start_import("601788_")
