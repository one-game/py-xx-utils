# -*- coding: utf-8 -*-

############################################
##
## defination of new crawler framework
## zhengquanshibaowang (stcn.com)
##
#############################################


import re
from XX_Crawler.XXNewsETL import *
from XX_Crawler.Utils import *
import logging
import time
from datetime import datetime


class STCNNewsCrawler(NewsCrawler):

    def __init__(self, list_url_tpl, data_path, website_name, b_class, checkpoint_filename, logger,checkpoint_saved_days):
        NewsCrawler.__init__(self, list_url_tpl, data_path, website_name,
                             b_class, logger=logger, checkpoint_filename=checkpoint_filename, checkpoint_saved_days=checkpoint_saved_days)
        self.kuaixun_list_pattern = re.compile(u"<li><p class=\"tit\"><a (.*?)>(.*?)<\/a><a href=\"(.*?)\" target=\"_blank\">(.*?)<\/a><span>\[(.*?)\]<\/span><\/p><\/li>")
        self.news_list_pattern = re.compile(u"<p class=\"tit\"><a href=\"(.*?)\" target=\"_blank\" title=\"(.*?)\">(.*?)<\/a><span>\[(.*?)\]<\/span><\/p>")
        self.base_url = list_url_tpl
        self.is_first_page = True
        self.cur_url = ""
        #self.b_class = b_class

    ##overwrite to generate news page filename
    def generate_news_filename(self, news_info):
        #filename = self.data_path + news_info["title"] + ".news"
        news_url = news_info["url"].split("//")[-1]
        class_name, date_no = news_url.split(".stcn.com")
        date_no = date_no.split(".")[0].replace("/","_")
        filename = "%s/%s%s.news" % (self.data_path, class_name, date_no)
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
            if self.b_class == "快讯":
                self.list_url_tpl += "index_%d.shtml"
            else:
                self.list_url_tpl += "%d.shtml"
        ret_url = self.list_url_tpl % (self.page_num)
        self.page_num += 1
        return ret_url


    ##overwrite to parse list page
    def parse_list_page(self, content):
        if self.b_class == "快讯":
            for _, subclass, url, title, pub_date in self.kuaixun_list_pattern.findall(content):
                # if self.last_date is None:
                #     self.last_date = pub_date
                news_info = {}
                news_info["url"] = url
                news_info["title"] = title
                news_info["pub_date"] = datetime.strptime(pub_date,"%Y-%m-%d %H:%M:%S")
                news_info["subclass"] = re.search("【(.*)】",subclass).group(1)
                self.logger.debug("found news %s (%s)" %(title, pub_date))
                yield news_info
        else:
            for url, title, _, pub_date in self.news_list_pattern.findall(content):
                news_info = {}
                news_info["url"] = url
                news_info["title"] = title
                news_info["pub_date"] = datetime.strptime(pub_date,"%Y-%m-%d %H:%M")
                self.logger.debug("found news %s (%s)" %(title, pub_date))
                yield news_info


class STCNNewsContentParser(NewsProcessor):

    def __init__(self, logger=None):
        NewsProcessor.__init__(self, logger)
        pass

    def multi_news_page(self, news_info, content):
        '''check if there are multi page in news
        if yes, yield next url, otherwise nothing
        '''
        page_info_pattern = re.compile('<div class=\"pagelist\">((.|\n)*?)<\/div>')
        page_data_pattern = re.compile("<a href=\"(.*?)\"(.*?)>(.*?)<\/a>")
        page_info = page_info_pattern.search(content)
        if page_info:
            cur_url = news_info["url"]
            page_info = page_info.group(1)
            page_info_data = page_data_pattern.findall(page_info)
            page_count = int(page_info_data[-2][0].split(".")[-2].split("_")[-1])
            self.logger.debug("there are %d pages for this news"%(page_count))
            for page_num in xrange(2, page_count+1):
                #next page url is 2017/1019/13700719.shtml =>2017/1019/13700719_2.shtml
                page_content = get(cur_url[:-6] +"_%d"%(page_num)+cur_url[-6:])
                if page_content is not None:
                    yield page_content

    def process(self, news_info, doc):
        '''parse news page
           date and source pattern:"<div class=\"info\">(.*?)<\/div>"
           content pattern :"<div class=\"txt_con\"(.*?)>(.*)<div class=\"adv\" style=\""
                        or :<div class=\"txt_con\"(.*?)>(.*)<\/div>(.*)<div class=\"(pic1|fenxiang)\"
           page count pattern：var currentPage = (\d+)(.|\n)*?var countPage = (\d+)
        '''
        try:
            page_content = doc.decode("gbk")
        except:
            page_content = doc
        news_page_pattern = re.compile(u"<div class=\"txt_con\"(.*?)>(.*)<div class=\"adv\" style=\"", re.DOTALL)
        news_page_pattern2 = re.compile(u"<div class=\"txt_con\"(.*?)>(.*?)<\/div>", re.DOTALL) #u"<div class=\"txt_con\"(.*?)>(.*)<\/div>(.*)<div class=\"(pic1|fenxiang|pagelist)\"", re.DOTALL)
        news_meta_pattern = re.compile(u"<div class=\"info\">(.*?)<\/div>")
        # Meta data
        meta_data = news_meta_pattern.search(page_content)
        source, date = "", ""
        if meta_data:
            try:
                date, source = meta_data.group(1).split("来源：")
                source_info = re.search("<a href=(.*)>(.*)<\/a>", source)
                if source_info:
                    source = source_info.group(2)
            except:
                date = meta_data.group(1)
            self.logger.debug("source=>"+source+",date=>"+date)
        else:
            self.logger.warning("Fail to get date and source info from url: %s"%(news_info["url"]))
        # hierarchy info
        hierarchy = ""
        news_hierarchy_pattern = re.compile(">(.*)<")
        try:
            hierarchy_info = re.search("<div class=\"website\">(.*?)<\/div>",page_content,re.DOTALL).group(1)
            hierarchy = news_hierarchy_pattern.findall(hierarchy_info)
            self.logger.debug("hierarchy=>"+"-".join(hierarchy[1:]))
        except:
            self.logger.warning("Fail to get hierarchy info from url: %s"%(news_info["url"]))
        # Pure news content
        try:
            pure_page = news_page_pattern.search(page_content).group(2)
        except:
            pure_page = news_page_pattern2.search(page_content).group(2)
        for next_page in self.multi_news_page(news_info, page_content):
            try:
                next_page = next_page.decode("gbk")
            except:
                pass
            pure_page += news_page_pattern2.search(next_page).group(2)

        news_info["source"] = source
        news_info["inner_page_date"] = date.strip()
        news_info["subclass"] = hierarchy[-1]
        news_info["hierarchy"] = "-".join(hierarchy[1:])
#        news_info["website_name"] = self.website_name
#        news_info["b_class"] = self.b_class
        return pure_page
