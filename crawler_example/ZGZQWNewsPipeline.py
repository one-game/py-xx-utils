# -*- coding: utf-8 -*-

############################################
##
## defination of new crawler framework
##
##
#############################################


import re
from XX_Crawler.XXNewsETL import *
from XX_Crawler.Utils import *
import logging
import time
from datetime import datetime


class ZGZQWNewsCrawler(NewsCrawler):

    def __init__(self, list_url_tpl, data_path, website_name, b_class, checkpoint_filename, logger,checkpoint_saved_days):
        NewsCrawler.__init__(self, list_url_tpl, data_path, website_name,
                             b_class, logger=logger, checkpoint_filename=checkpoint_filename, checkpoint_saved_days=checkpoint_saved_days)
#        self.b_class = b_class
        self.yw_list_pattern = re.compile("<li><span class=\"time\">\[(.*)\]<\/span> <a href=\"(.*)\" target=\"_blank\" title=\"(.*?)\">(.*)<\/a><\/li>")
        self.gsxw_list_pattern = re.compile("<li><span class=\"time\">(.*)<\/span> <a href=\"(.*)\" target=\"_blank\" title=\"(.*?)\">(.*)<\/a><\/li>")
        self.base_url = list_url_tpl #"http://news.cnstock.com/news/sns_yw/"
        self.is_first_page = True
#        self.cur_url = ""


    ##overwrite to generate news page filename
    def generate_news_filename(self, news_info):
        news_url = news_info["url"]
        news_url = news_url.replace(",","_").replace("-","_")
        filename = self.data_path + news_url.split("cnstock.com/")[1].split(".")[0].replace("/","_") + ".news"
        self.logger.debug("generate news filename "+ filename)
        return filename

    ##overwrite to generate list page filename
    def generate_list_filename(self):
        filename = self.data_path + self.website_name+"_"+self.b_class+"_"+str(int(time.time()))+".list"
        self.logger.debug("generate list filename "+ filename)
        return filename

    ##overwrite to generate new list page url
    def generate_next_list_url(self):
        if self.page_num == 0:
            self.page_num += 1
            self.list_url_tpl += "%d"
        ret_url = self.list_url_tpl % (self.page_num)
        self.page_num += 1
        return ret_url

    ##overwrite to parse list page
    def parse_list_page(self, content):
        if self.b_class == "要闻":
            list_pattern = self.yw_list_pattern
        elif self.b_class == "公司聚焦":
            list_pattern = self.gsxw_list_pattern
        for pub_date, url, title, _ in list_pattern.findall(content):
            news_info = {}
            news_info["url"] = url
            news_info["title"] = title
            # news_info["pub_date"] = pub_date
            if self.b_class == "要闻":
                news_info["pub_date"] = datetime.strptime(pub_date,"%Y-%m-%d %H:%M")
            elif self.b_class == "公司聚焦":
                news_info["pub_date"] = datetime.strptime(pub_date,"%Y-%m-%d")
            self.logger.debug("found news %s (%s)" %(title, pub_date))
            yield news_info

    #
    def generate_url_from_list(self, content):
        news_info_list = [news_info for news_info in self.parse_list_page(content)]
        if len(news_info_list) == 0:
            yield None
        # no_check_point = False
        news_start_flag = False
        old_news_count = 0
        if self.check_point is None:
            self.check_point = {}
            # no_check_point = True
        for news_info in reversed(news_info_list):
            # If the url is not a news page, skip it
            if news_info["url"][-4:] != ".htm":
                continue
            news_title = news_info["title"]
            if  news_title in self.check_point:
                old_news_count += 1
                self.logger.debug("%s in check_point, continue" % news_title)
                continue
            self.check_point[news_title] = news_info["pub_date"]
            self.logger.debug("add %s to check_point" % news_title)
            yield news_info
            #break
        self.logger.debug("finish parse list page %d" % (self.page_num))
        if old_news_count > 3:
            self.logger.debug("this page has more than 3 old news stop crawling")
            yield None
        if self.no_check_point and self.page_num > 3:
            self.logger.debug("no last check point info. one page finished")
            yield None


class ZGZQWNewsContentParser(NewsProcessor):

    def __init__(self, logger=None):
        NewsProcessor.__init__(self, logger)
        pass

    # ##check if there are multi page in news
    # def multi_news_page(self, news_info, content):
    #     '''check if there are multi page in news
    #     if yes, yield next url, otherwise nothing
    #     '''
    #     page_info_pattern = re.compile('var currentPage = (\d+)(.|\n)*?var countPage = (\d+)')
    #     page_info_data = page_info_pattern.search(content)
    #     if page_info_data:
    #         #print page_info_data.group(1)
    #         page_count = int(page_info_data.group(3))
    #         logging.debug("there are %d pages for this news"%(page_count))
    #         cur_url = news_info["url"]
    #         for page_num in xrange(1, page_count):
    #             #next page url is t2017-10-09_32432432.html =>t2017-10-09_32432432_1.html
    #             page_content = get(cur_url[:-5] +"_%d"%(page_num)+cur_url[-5:])
    #             if page_content is not None:
    #                 yield page_content

    def process(self, news_info, doc):
        '''parse news page
        '''
        page_content = doc.decode("gbk")
    	if re.findall("下一页", page_content) or re.findall(u"下一页", page_content):
            self.logger.warning("There is next page of news %s"%(news_info["url"]))
        # meta data, including date, author, source
        news_meta_pattern = re.compile("<span class=\"timer\">(.*)<\/span>(.|\n)*?<span class=\"source\">(.*)<\/span>(.|\n)*?<span class=\"author\">(.*)<\/span>")
        meta_data = news_meta_pattern.search(page_content)
        if meta_data:
            #print meta_data.groupdict()
            date = meta_data.group(1)
            source = meta_data.group(3)
            author = meta_data.group(5)
        else:
            self.logger.warning("Fail to get date, source, author info from url: %s"%(news_info["url"]))
            date, source, author = "", "", ""
        source_info = re.search("<a href=(.*)>(.*)<\/a>", source)
        if source_info:
            source = source_info.group(2)
        self.logger.debug("author=>"+author+",source=>"+source+",date=>"+date)
        # keywords
        news_keywords_pattern = re.compile("<meta name=\"keywords\" content=\"(.*)\" \/>")
        keywords_info = news_keywords_pattern.search(page_content)
        if keywords_info:
            keywords = keywords_info.group(1)
            self.logger.debug("keywords=>"+keywords)
        else:
            keywords = ""
            self.logger.warning("Fail to get keywords from url: %s"%(news_info["url"]))
        # hierarchy directory of the news in cnstock website
        news_hierarchy_pattern = re.compile(">(.*)<")
        hierarchy_info = re.search("<div id=\"cms_output_nav\" style=\"display:none;\">(.*?)<\/div>", page_content)
        if hierarchy_info:
            hierarchy = "-".join([news_hierarchy_pattern.search(hie).group(1) for hie in hierarchy_info.group(1).split("-&gt;")])
            self.logger.debug("hierarchy=>"+hierarchy)
        else:
            hierarchy = ""
            self.logger.warning("Fail to get hierarchy info from url: %s"%(news_info["url"]))
        # news pure content
        news_content_pattern = re.compile("<div class=\"content\" id=\"qmt_content_div\">(.*)<\/div>(\s)*<div class=\"bullet\">",re.DOTALL)
        news_content = news_content_pattern.search(page_content)
        try:
            news_info["inner_page_date"] = datetime.strptime(date,"%Y-%m-%d %H:%M:%S")
        except:
            self.logger.warning("Unable to parse date %s in format Y-m-d H:M:S"%(date))
            news_info["inner_page_date"] = date
        news_info["source"] = source.split(u"：")[-1]
        news_info["author"] = author.split(u"：")[-1]
        news_info["keywords"] = keywords
        news_info["hierarchy"] = hierarchy
#        news_info["website_name"] = self.website_name
#        news_info["b_class"] = self.b_class
        if not news_content:
            self.logger.warning("Content of news %s is none, url: %s"%(news_info["title"],news_info["url"]))
            return ""
        return news_content.group(1).strip()
