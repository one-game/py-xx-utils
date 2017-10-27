# -*- coding: utf-8 -*-

'''crawl 163(wangyi)
'''


import re
from XX_Crawler.XXNewsETL import *
from XX_Crawler.Utils import *
import logging
import json
import time
from datetime import datetime


class WYNewsCrawler(NewsCrawler):

    def __init__(self, list_url_tpl, data_path, website_name, b_class, checkpoint_filename, logger,checkpoint_saved_days):
        NewsCrawler.__init__(self, list_url_tpl, data_path, website_name,
                             b_class, logger=logger, checkpoint_filename=checkpoint_filename, checkpoint_saved_days=checkpoint_saved_days)
        self.list_pattern = re.compile("<dl>(.|\n)*?<dt><a href=\"(.*)\">(.*)<\/a><\/dt>(.|\n)*?<span(.|\n)*?>(.*)<\/span>(.|\n)*?<\/dl>")
        self.base_url = list_url_tpl #"http://www.cs.com.cn/gppd/"
        self.is_first_page = True
        self.cur_url = ""
        self.b_class = b_class

    ##overwrite to generate news page filename
    def generate_news_filename(self, news_info):
        #filename = self.data_path + news_info["title"] + ".news"
        class_name = self.base_url.split("/")[-1].split(".")[0]
        date_no = news_info["url"].split("/")[-1].split(".")[0]
        filename = "%s/%s_%s.news" % (self.data_path, class_name, date_no)
        logging.debug("generate news filename "+ filename)
        return filename

    ##overwrite to generate list page filename
    def generate_list_filename(self):
        filename = self.data_path + self.website_name+"_"+self.b_class+"_"+str(int(time.time()))+".list"
        logging.debug("generate list filename "+ filename)
        return filename

    ##overwrite to generate new list page url
    def generate_next_list_url(self):
        if self.page_num == 0:
            self.page_num += 1
            ret_url = self.list_url_tpl
            self.list_url_tpl = ".".join(self.list_url_tpl.split(".")[:-1]) + "_%d."+self.list_url_tpl.split(".")[-1]
            return ret_url
        ret_url = self.list_url_tpl % (self.page_num)
        self.page_num += 1
        return ret_url

    ##overwrite to parse list page
    def parse_list_page(self, content):
        content = content.decode("gbk","ignore").encode("utf-8")
        json_part_pattern = re.compile("data_callback\((\[(.|\n)*\])\)")
        matched = json_part_pattern.search(content)
        if matched:
            news_list = json.loads(matched.group(1))
            logging.debug("found %d news in page %d"%(len(news_list), self.page_num))
            for news_info in news_list:
                news_info["url"] = news_info["docurl"]
                news_info["pub_date"] = datetime.strptime(news_info["time"],"%m/%d/%Y %H:%M:%S")
                logging.debug("found news %s=> %s"%(news_info["title"], news_info["url"]))
                yield news_info
                #break


class WYNewsContentParser(NewsProcessor):

    def __init__(self, logger=None):
        NewsProcessor.__init__(self, logger)
        pass

    def process(self, news_info, doc):
        page_content = doc.decode("gbk","ignore").encode("utf-8")
        page_content_pattern = re.compile("<div class=\"post_text\".*?>((.|\n)*?)<\/div>(.|\n)*?<div class=\"post_btmshare\">")
        page_date_pattern = re.compile("<div class=\"post_time_source\">(.|\n)*?(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).+来源.+?>(.*?)<")
        date_data = page_date_pattern.search(page_content)
        date_str = ""
        source = ""
        if date_data:
            date_str = date_data.group(2)
            source = date_data.group(3)
        content_data = page_content_pattern.search(page_content)
        if content_data:
            pure_page = content_data.group(1)
            news_info["inner_page_date"] = date_str
            news_info["source"] = source
            del news_info["keywords"]
            logging.debug("source=>"+source+"date=>"+date_str)
            return pure_page
        return None