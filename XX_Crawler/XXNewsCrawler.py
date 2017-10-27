# -*- coding: utf-8 -*-

############################################
##
## defination of new crawler framework
##
##
#############################################

import requests
import time
import logging
import json
import cPickle as pickle
from datetime import datetime
from XX_ES.XX_ESImporter.ESImporter import ESImporter


class NewsProcesser():

    def __init__(self):
        pass

    def process(self, news_info, doc):
        return doc


class NewsUploader():

    def __init__(self):
        pass


class NewsCrawler:

    debug = False
    

    def __init__(self,
                 list_url_tpl,
                 data_path,
                 website_name,
                 b_class,
                 requests_interval = 1,
                 banned_interval = 5,
                 max_request_retry = 5,
                 log_level = logging.INFO, #logging.DEBUG,
                 log_filename = "./news_crawler.log",
                 checkpoint_filename = None,
                 ):
        self.requests_interval = requests_interval
        self.exception_interval = requests_interval
        self.banned_interval = banned_interval
        self.max_request_retry = max_request_retry
        self.list_url_tpl = list_url_tpl
        self.page_num = 0
        self.data_path = data_path
        self.doc_counter = 0
        self.website_name = website_name
        self.b_class = b_class
        logging.basicConfig(level=log_level,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=log_filename,
                            filemode='a'
                            )
        self.checkpoint_filename = checkpoint_filename
        ##load check point
        self.check_point = self.load_checkpoint()

        ##es_importer
        es_server_list = [
            {'host': '192.168.2.21', 'port': 9200},
            {'host': '192.168.2.22', 'port': 9200},
            {'host': '192.168.2.23', 'port': 9200},
            {'host': '192.168.2.24', 'port': 9200}
        ]
        index_name = "nlp_stock_news_v1"
        type_name = "news"
        self.db_importer = ESImporter(es_server_list, index_name, type_name)
        self.processors = []

        #statistics
        self.total_count = 0
        self.download_failed_count = 0
        self.download_failed_list = []
        self.parse_failed_count = 0
        self.parse_failed_list = []
        self.upload_failed_count = 0 
        self.upload_failed_list = []


    def __del__(self):
        ##dump check point 
        #self.dump_checkpoint()
        pass    

    def load_checkpoint(self):
        try:
            if self.checkpoint_filename is None:
                self.checkpoint_filename = self.__class__.__name__+".ckpt"
            with open(self.checkpoint_filename,"r") as fd:
                return pickle.loads(fd.read())
        except:
            return None

    def dump_checkpoint(self):
        with open(self.checkpoint_filename,"w") as fd:
            fd.write(pickle.dumps(self.check_point))
        logging.debug("finished dumping checkpoint")

    def run(self):
        logging.info("stat:task:%s:%s:start:"%(self.website_name, self.b_class)+str(datetime.now()))
        while True:
            #generate list page url
            list_url = self.generate_next_list_url()
            logging.debug("start to download %s" % (list_url))
            #fetching list page content
            content = self.get(list_url)
            #generate list page filename
            filename = self.generate_list_filename()
            if content is None:
                logging.debug("list page is none")
                self.task_finished()
                self.dump_checkpoint()
                return
            #write list page to local fs
            self.write_to_file(filename, content)
            #iterate all news in the list page
            for news_info in self.generate_url_from_list(content):
                if news_info is None:
                    #when news_info is None, it indicates that updating
                    #is finished
                    #update finished
                    logging.debug("prepare calling task_finished function")
                    self.task_finished()
                    self.dump_checkpoint()
                    return True
                news_url = news_info["url"]
                #fetching news page
                logging.info("stat:download:start:%s"%(news_url))
                content = self.get(news_url)
                if content is None:
                    #todo:
                    logging.info("stat:download:end:failed")
                    #logging.warning("Failed to download %s with content is None"%(news_url))
                    continue
                #processing news page
                self.process_news_page(news_info, content)
        

    def process_news_page(self, news_info, content):
        '''todo: process news page including 3 steps
        step 1: write to local fs
        step 2: parse content
        step 3: upload to es
        '''
        filename = self.generate_news_filename(news_info)
        if filename is None:
            logging.warning("generate news filename falsed for %s"%(news_info["url"]))
            return False
        self.write_to_file(filename, content)
        #todo: parse news page
        logging.info("stat:parse:start:%s:%s"%(filename, news_info["url"]))
        pure_content = self.parse_news_page(news_info, content)
        #pure_content = {"url":"xx","title":"xx","pub_date":"xx","source":"xx","author":"xx","content":"xx"}
        if pure_content is None:
            logging.info("stat:parse:end:failed")
            return False
        doc = self.assemble_news_data(news_info, pure_content)
        #self.write_to_file(self.generate_news_filename(news_info)+".dict", json.dumps(doc))
        #todo: process doces
        doc = self.process_doc(doc)
        ##upload
        self.upload_to_es(doc)

    def add_processor(self, processor):
        if not isinstance(processor, NewsProcesser):
            return False
        self.processors.append(processor)
        return len(processor)

    def process_doc(self, doc):
        logging.info("stat:process:start:%s"%(doc["_id"]))
        for processor in self.processors:
            doc = processor.process(doc)
            if doc is None:
                logging.info("stat:process:end:failed")
                return None
        return doc

    def upload_to_es(self, doc):
        self.db_importer.insert_to_es(doc)


    def generate_news_id(self, news_info, content):
        return self.generate_news_filename(news_info).split("/")[-1].split(".")[0]

    def assemble_news_data(self, news_info, content):
        ret_dict = {}
        ret_dict["_id"] = self.generate_news_id(news_info, content)
        ret_dict["content"] = content
        ret_dict["meta"] = news_info
        return ret_dict

    def get(self, url, timeout=30, header={}):
        retry_count = 0
        while retry_count < self.max_request_retry:
            try:
                retry_count += 1
                logging.debug("getting "+url)
                page = requests.get(url, timeout=timeout, headers=header)
                if page.status_code != 200:
                    logging.warning("url:%s return %d"%(url, page.status_code))
                    return None
                if not self.is_page_banned(page.content):
                    time.sleep(self.requests_interval)
                    self.doc_counter += 1
                    return page.content
                else:
                    time.sleep(self.banned_interval)
            except Exception as e:
                logging.debug("get exception : "+str(e))
                time.sleep(self.exception_interval)
        return None

    def write_to_file(self, filename, content):
        with open(filename, "w") as fd:
            fd.write(content)
        logging.debug("finished writing file "+filename)

    ##overwrite function
    def task_finished(self):
        self.db_importer.commit_to_es()
        logging.info("stat:task:end:"+str(datetime.now()))
        pass

    ##overwrite to generate news page filename
    def generate_news_filename(self, news_info):
        return ""

    ##overwrite to generate list page filename
    def generate_list_filename(self):
        logging.debug("calling base generate list filename function")
        return ""

    ##overwrite to generate new list page url
    def generate_next_list_url(self):
        self.page_num += 1
        return self.list_url_tpl % (self.page_num)

    ##overwrite to parse news detail page
    def parse_news_page(self, news_info, page_content):
        pass

    ##overwrite to parse list page
    def parse_list_page(self, content):
        pass

    ##overwrite to check if the news needs to be updated
    def news_need_update(self, news_info):
        return False

    ##overwrite to check if ip is banned
    def is_page_banned(self, content):
        return False

    def generate_url_from_list(self, content):
        '''this function generate news_info by parsing the list page
           when the old news are meet return None to end the whole process
           return :
               this function yield news_info which is a dict whoes keys
               are url, title, 
        '''
        for news_info in self.parse_list_page(content):
            if not self.news_need_update(news_info):
                yield None
                break
            yield news_info
        pass
