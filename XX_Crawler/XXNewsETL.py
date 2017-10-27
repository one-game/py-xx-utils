# -*- coding: utf-8 -*-

############################################
##
# defination of new crawler framework
##
##
#############################################


import requests
import time
import logging
import sys
import traceback
import cPickle as pickle
from datetime import datetime
from datetime import timedelta
from XX_ES.XX_ESImporter.ESImporter import ESImporter
from multiprocessing import Process, Pool
from Utils import *
import os


class NewsProcessor():
    '''
    base news process
    main logic in process function which take
    news_info and doc as parameters
    '''

    def __init__(self, logger):
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger
        pass

    def process(self, news_info, doc):
        return doc

    def process_finish(self):
        pass

    class ProcessorException(Exception):
        """Exception for processors
        """
        pass


class AssembleNewsProcessor(NewsProcessor):
    '''
    assemble news processor which is used for
    assemble news meta data and parsed content
    '''

    def __init__(self, logger=None):
        NewsProcessor.__init__(self, logger)
        pass

    def generate_news_id(self, news_info, content):
        try:
            news_id = news_info["filename"].split("/")[-1].split(".")[0]
            return news_id
        except:
            # todo print warning
            return None

    def process(self, news_info, doc):
        ret_dict = {}
        ret_dict["_id"] = self.generate_news_id(news_info, doc)
        ret_dict["content"] = doc
        ret_dict["meta"] = news_info
        return ret_dict


class NewsUploader():

    # , es_server_list, index_name, type_name):
    def __init__(self, es_server_list, index_name, type_name, logger=None):
        es_server_list = es_server_list
        index_name = index_name
        type_name = type_name
        self.db_importer = ESImporter(es_server_list, index_name, type_name)
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger
        pass

    def convert_to_string(self, doc):
        for k, v in doc.iteritems():
            if isinstance(v, datetime):
                doc[k] = datetime.strftime(v, "%y-%m-%d %H:%M:%S")
            elif isinstance(v, dict):
                doc[k] = self.convert_to_string(v)

    def upload(self, doc):
        # process doc convert datetime to str
        self.convert_to_string(doc)
        self.db_importer.insert_to_es(doc)
        pass

    def commit(self):
        self.db_importer.commit_to_es()
        pass


class ESUploadProcessor(AssembleNewsProcessor, NewsUploader):
    '''upload doc to es
    '''

    def __init__(self, logger, es_server_list, index_name, type_name):
        NewsProcessor.__init__(self, logger)
        NewsUploader.__init__(self, es_server_list,
                              index_name, type_name, logger)
        self.es_server_list = es_server_list
        self.index_name = index_name
        self.type_name = type_name

        pass

    def process(self, news_info, doc):
        try:
            ret_dict = {}
            ret_dict["_id"] = self.generate_news_id(news_info, doc)
            ret_dict["content"] = doc
            ret_dict["meta"] = news_info
            self.upload(ret_dict)
            return doc
        except Exception as e:
            raise NewsProcessor.ProcessorException(
                "Failed to upload to es :" + e.message)
        pass

    def process_finish(self):
        try:
            self.commit()
        except Exception as e:
            raise NewsProcessor.ProcessorException(
                "Failed to commit :" + e.message)
        pass


class NewsCrawler:

    debug = False

    def __init__(self,
                 list_url_tpl,
                 data_path,
                 website_name,
                 b_class,
                 requests_interval=1,
                 banned_interval=5,
                 max_request_retry=5,
                 logger=None,
                 checkpoint_filename=None,
                 checkpoint_saved_days=3,
                 ):
        self.requests_interval = requests_interval
        self.exception_interval = requests_interval
        self.banned_interval = banned_interval
        self.max_request_retry = max_request_retry
        self.list_url_tpl = list_url_tpl
        self.page_num = 0
        self.data_path = data_path
        # check if the data path exists
        if not os.path.exists(data_path):
            os.mkdir(data_path)
        self.doc_counter = 0
        self.website_name = website_name
        self.b_class = b_class
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger
        self.checkpoint_filename = checkpoint_filename
        # load check point
        self.check_point = self.load_checkpoint()
        self.no_check_point = True if self.check_point is None else False
        self.checkpoint_saved_days = checkpoint_saved_days

    def __del__(self):
        # dump check point
        # self.dump_checkpoint()
        pass

    def load_checkpoint(self):
        try:
            if self.checkpoint_filename is None:
                self.checkpoint_filename = self.__class__.__name__ + ".ckpt"
            with open(self.checkpoint_filename, "r") as fd:
                return pickle.loads(fd.read())
        except:
            return None

    def dump_checkpoint(self):
        if self.check_point is not None:
            savedDay = timedelta(days=self.checkpoint_saved_days)
            now = datetime.now()
            self.check_point = dict(filter(lambda items: items[1] > (
                now - savedDay), self.check_point.items()))
            with open(self.checkpoint_filename, "w") as fd:
                fd.write(pickle.dumps(self.check_point))
            self.logger.debug("finished dumping checkpoint")

    def run(self):
        while True:
            # generate list page url
            list_url = self.generate_next_list_url()
            self.logger.debug("start to download %s" % (list_url))
            # fetching list page content
            content = self.get(list_url)
            # generate list page filename
            filename = self.generate_list_filename()
            if content is not None:
                # write list page to local fs
                self.write_to_file(filename, content)
                # iterate all news in the list page
                update_finished = False
                for news_info in self.generate_url_from_list(content):
                    if news_info is not None:
                        news_url = news_info["url"]
                        # fetching news page
                        self.logger.info("stat:download:start:%s" % (news_url))
                        content = self.get(news_url)
                        if content is None:
                            # todo:
                            self.logger.info("stat:download:end:failed")
                            #logging.warning("Failed to download %s with content is None"%(news_url))
                            continue
                        # processing news page
                        filename = self.generate_news_filename(news_info)
                        if filename is None:
                            self.logger.warning(
                                "generate news filename falsed for %s" % (news_info["url"]))
                            # return False
                            continue
                        news_info["filename"] = filename
                        news_info["website_name"] = self.website_name
                        news_info["b_class"] = self.b_class
                        self.write_to_file(
                            filename + ".news_info", pickle.dumps(news_info))
                        self.write_to_file(filename, content)
                        yield news_info, content
                        #self.process_news_page(news_info, content)
                    else:
                        # if news_info is None
                        #
                        update_finished = True
                        break
                if update_finished:
                    break
                continue
            break
        self.task_finished()
        self.dump_checkpoint()

    def get(self, url, timeout=30, header={}):
        retry_count = 0
        while retry_count < self.max_request_retry:
            try:
                retry_count += 1
                self.logger.debug("getting " + url)
                page = requests.get(url, timeout=timeout, headers=header)
                if page.status_code != 200:
                    self.logger.warning("url:%s return %d" %
                                        (url, page.status_code))
                    return None
                if not self.is_page_banned(page.content):
                    time.sleep(self.requests_interval)
                    self.doc_counter += 1
                    return page.content
                else:
                    time.sleep(self.banned_interval)
            except Exception as e:
                self.logger.debug("get exception : " + str(e))
                time.sleep(self.exception_interval)
        return None

    def write_to_file(self, filename, content):
        with open(filename, "w") as fd:
            fd.write(content)
        self.logger.debug("finished writing file " + filename)

    # overwrite function
    def task_finished(self):
        pass

    # overwrite to generate news page filename
    def generate_news_filename(self, news_info):
        return ""

    # overwrite to generate list page filename
    def generate_list_filename(self):
        return ""

    # overwrite to generate new list page url
    def generate_next_list_url(self):
        self.page_num += 1
        return self.list_url_tpl % (self.page_num)

    # overwrite to parse list page
    def parse_list_page(self, content):
        pass

    # overwrite to check if the news needs to be updated
    def news_need_update(self, news_info):
        return False

    # overwrite to check if ip is banned
    def is_page_banned(self, content):
        return False

    def generate_url_from_list_ex(self, content):
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

    def generate_url_from_list(self, content):
        news_info_list = [
            news_info for news_info in self.parse_list_page(content)]
        if len(news_info_list) == 0:
            yield None
        news_start_flag = False
        old_news_count = 0
        if self.check_point is None:
            self.check_point = {}
        for news_info in reversed(news_info_list):
            news_title = news_info["title"]
            if news_title in self.check_point:
                old_news_count += 1
                self.logger.debug("%s in check_point, continue" % news_title)
                continue
            self.check_point[news_title] = news_info["pub_date"]
            self.logger.debug("add %s to check_point" % news_title)
            yield news_info
            # break
        self.logger.debug("finish parse list page %d" % (self.page_num))
        if old_news_count > 3:
            self.logger.debug(
                "this page has more than 3 old news stop crawling")
            yield None
        if self.no_check_point and self.page_num > 3:
            self.logger.debug("no last check point info. one page finished")
            yield None


class NewsPipeline():

    def __init__(self, conf):
        '''
        conf = {"websites":[
          {
            "domain":"money.163.com",
            "pipelines":[
              {
                  "crawler":{"name":"XXNewsCrawler.NewsCralwer","params":{"start_url":"class_name"}},
                  "transformaer":[{"name":"XXNewsCrawler.XX,"params":""}],
                  "uplaoder":{"name":"","params":""}
              },
              {
                  "crawler":{"name":"XXNewsCrawler.NewsCralwer","params":{"start_url":"class_name_B"}},
                  "transformaer":{"name":"XXNewsCrawler.XX,"params":""},
                  "uplaoder":{"name":"","params":""}
              }
            ]
          }
        ]}
        '''
        # check format of configuration file
        if "websites" not in conf:
            raise Exception("no websites field in conf")

        self.conf = conf
        pass

    def run(self):
        '''
        run in multi process
        same domain in the same process
        '''
        p_list = []
        # logger = InitLog("pipeline.log", logging.getLogger("pipeline.log"), "info")
        for domain_info in self.conf["websites"]:
            # print "start pipeline for ", domain_info["domain_name"]
            nw = NewsWorker(domain_info["pipelines"],
                            domain_info["domain_name"],
                            )
            nw.start()
            p_list.append(nw)
            #break
        for p in p_list:
            p.join()


class NewsWorker(Process):

    def __init__(self, conf, domain_name):
        Process.__init__(self)
        self.conf = conf
        self.domain_name = domain_name
        # todo: check conf format

    def run(self):
        '''run multi pipelines for the same domain in same process
        '''
        for pipeline_conf in self.conf:
            # self.base_logger.info("stat:task:%s:%s:start:" % (
            #         self.domain_name, pipeline_conf["name"]) + str(datetime.now()))
            try:
                # init logging module
                log_level = pipeline_conf["log_level"]
                log_filename = pipeline_conf["log_filename"]
                logger = InitLog(log_filename, logging.getLogger(
                    log_filename), log_level)
                logger.info("stat:task:%s:%s:start:" % (
                    self.domain_name, pipeline_conf["name"]) + str(datetime.now()))
                pipeline_conf["crawler"]["params"]["logger"] = logger
                #pipeline_conf["crawler"]["params"]["logger"] = logger
                pipeline_conf["uploader"]["params"]["logger"] = logger
                # assemble pipeline
                crawler = import_object(
                    pipeline_conf["crawler"]["name"], pipeline_conf["crawler"]["params"])
                transformers = []
                for transformer_info in pipeline_conf["transformers"]:
                    transformer_info["params"]["logger"] = logger
                    transformers.append(import_object(
                        transformer_info["name"], transformer_info["params"]))
                transformers.append(AssembleNewsProcessor())
                uploader = import_object(
                    pipeline_conf["uploader"]["name"], pipeline_conf["uploader"]["params"])
                for news_info, doc in crawler.run():
                    if news_info is None:
                        continue
                    logger.info("stat:transform:start:" + str(datetime.now()))
                    for transformer in transformers:
                        try:
                            doc = transformer.process(news_info, doc)
                        except NewsProcessor.ProcessorException as pe:
                            logger.info(
                                "stat:transform:end:failed:" + pe.message)
                            continue
                    logger.info("stat:transform:end:success:" +
                                str(datetime.now()))
                    uploader.upload(doc)
                uploader.commit()
                for transformer in reversed(transformers):
                    try:
                        transformer.process_finish()
                    except NewsProcessor.ProcessorException as e:
                        logger.warning("stat:transform:finish_failed")
                logger.info("stat:task:end:" + str(datetime.now()))
                # self.base_logger.info("stat:task:end:" + str(datetime.now()))
                #break
            except Exception as e:
                logger.info("stat:task:end:failed:" + e.message)
                traceback.print_exc()
