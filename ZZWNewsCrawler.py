# -*- coding: utf-8 -*-

'''crawl zhongzhengwang
'''


import re
from XX_Crawler.XXNewsCrawler import NewsCrawler
import logging
import json
import time


class ZZWNewsCrawler(NewsCrawler):

    def __init__(self, list_url_tpl, data_path, website_name, b_class, checkpoint_filename):
        NewsCrawler.__init__(self, list_url_tpl, data_path,website_name, checkpoint_filename=checkpoint_filename)
        self.list_pattern = re.compile("<dl>(.|\n)*?<dt><a href=\"(.*)\">(.*)<\/a><\/dt>(.|\n)*?<span(.|\n)*?>(.*)<\/span>(.|\n)*?<\/dl>")
        self.base_url = list_url_tpl #"http://www.cs.com.cn/gppd/"
        self.is_first_page = True
        self.cur_url = ""
        self.b_class = b_class

    # def task_finished(self):
    #     pass
    #     # logging.debug("task_finished "+str(self.last_date))
    #     # if self.last_date is not None:
    #     #     if self.check_point is None:
    #     #         self.check_point = {}
    #     #     self.check_point["last_date"] = self.last_date

    ##overwrite to generate news page filename
    def generate_news_filename(self, news_info):
        #filename = self.data_path + news_info["title"] + ".news"
        class_name = self.base_url.split(u"/")[-2]
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
            self.list_url_tpl += "index_%d.shtml"
            return ret_url
        ret_url = self.list_url_tpl % (self.page_num)
        self.page_num += 1
        return ret_url

    ##overwrite to parse news detail page
    def parse_news_page(self, news_info, page_content):
        '''parse news page
           auther and source pattern:<span><em>(.*?)：<\/em>(.*?)<\/span>
           date pattern : <span class="Ff">(.*?)<\/span>
           content pattern :<div class="artical_c">(.|\n)*?<!-- 附件列表 -->
           page count pattern：var currentPage = (\d+)(.|\n)*?var countPage = (\d+)
        '''
        page_content = page_content.decode("gbk")
        news_page_pattern = re.compile(u'<div class=\"artical_c\">((.|\n)*?)<!-- 附件列表 -->')
        news_meta_pattern = re.compile(u'<span><em>作者：</em>(.*?)</span><span><em>来源：<\/em>(.*?)<\/span>')
        news_date_pattern = re.compile(u'<span class="Ff">(.*?)<\/span>')
        meta_data = news_meta_pattern.search(page_content)
        auther = ""
        source = ""
        date = ""
        if meta_data:
            #print meta_data.groupdict()
            auther = meta_data.group(1)
            source = meta_data.group(2)
        date_data = news_date_pattern.search(page_content)
        if date_data:
            date = date_data.group(1)
        pure_page = news_page_pattern.search(page_content).group(1)
        for next_page in self.multi_news_page(page_content):
            next_page = next_page.decode("gbk")
            pure_page += news_page_pattern.search(next_page).group(1)
        logging.debug("auther=>"+auther+"\nsource=>"+source+"\ndate=>"+date)
        news_info["author"] = auther
        news_info["source"] = source
        news_info["inner_page_date"] = date
        news_info["website_name"] = self.website_name
        news_info["b_class"] = self.b_class
        return pure_page

    ##check if there are multi page in news
    def multi_news_page(self, content):
        '''check if there are multi page in news
        if yes, yield next url, otherwise nothing
        '''
        page_info_pattern = re.compile('var currentPage = (\d+)(.|\n)*?var countPage = (\d+)')
        page_info_data = page_info_pattern.search(content)
        if page_info_data:
            #print page_info_data.group(1)
            page_count = int(page_info_data.group(3))
            logging.debug("there are %d pages for this news"%(page_count))
            for page_num in xrange(1, page_count):
                #next page url is t2017-10-09_32432432.html =>t2017-10-09_32432432_1.html
                page_content = self.get(self.cur_url[:-5] +"_%d"%(page_num)+self.cur_url[-5:])
                if page_content is not None:
                    yield page_content

    ##overwrite to parse list page
    def parse_list_page(self, content):
        for _, url, title, _ ,_,pub_date, _ in self.list_pattern.findall(content):
            # if self.last_date is None:
            #     self.last_date = pub_date
            news_info = {}
            news_info["url"] = self.base_url+url
            news_info["title"] = title.decode("gbk")
            news_info["pub_date"] = pub_date #time.strptime(pub_date,"%y-%m-%d %H:%M")
            logging.debug("found news %s (%s)" %(title, pub_date))
            yield news_info

    ##overwrite to check if the news needs to be updated
    # def news_need_update(self, news_info):
    #     if self.check_point is None:
    #         last_date = time.strptime("17-10-10 16:00","%y-%m-%d %H:%M")
    #     else:
    #         last_date = time.strptime(self.check_point["last_date"],"%y-%m-%d %H:%M")
    #     if news_info["pub_date"] <= last_date:
    #         logging.debug("news date is earlier than last update date")
    #         return False
    #     return True

    ##overwrite to check if ip is banned
    # def is_page_banned(self, content):
    #     return False

    def generate_url_from_list(self, content):
        news_info_list = [news_info for news_info in self.parse_list_page(content)]
        title_list = [news_info["title"] for news_info in news_info_list]
        last_three_titles = title_list[-3:]
        if self.check_point is None:
            last_title_list = []
        else:
            last_title_list = self.check_point.get("last_title_list",[])
        news_start_flag = False
        old_news_count = 0
        for news_info in reversed(news_info_list):
            news_title = news_info["title"]
            if not news_start_flag and news_title in last_title_list:
                old_news_count += 1
                continue
            news_start_flag = True
            self.cur_url = news_info["url"]
            yield news_info

        if self.is_first_page:
            if not self.check_point:
                self.check_point = {}
            self.check_point["last_title_list"] = title_list
            logging.debug("assigne check_point")
            self.is_first_page = False
        if old_news_count > 3:
            logging.debug("this page has more than 3 old news stop crawling")
            yield None
        elif not last_title_list:
            logging.debug("no last check point info. one page finished")
            yield None





if __name__ == "__main__":
    url_tpls = {
                u"公司":"http://www.cs.com.cn/ssgs/",
                u"市场":"http://www.cs.com.cn/gppd/",
                u"宏观":"http://www.cs.com.cn/xwzx/"
                }
    for b_class, url in url_tpls.items():
        crawler = ZZWNewsCrawler(url, "./data/",u"中证网", b_class, url.split("/")[-2]+".ckpt")
        crawler.run()
