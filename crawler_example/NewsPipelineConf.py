# -*- coding: utf-8 -*-

es_uploader_conf = {
    "name": "XX_Crawler.XXNewsETL.NewsUploader",
    "params": {
        "es_server_list": [
            {'host': '192.168.2.21', 'port': 9200},
            {'host': '192.168.2.22', 'port': 9200},
            {'host': '192.168.2.23', 'port': 9200},
            {'host': '192.168.2.24', 'port': 9200}
        ],
        "index_name": "company_news_result_v1",
        "type_name": "news"
    }
}

es_uploader_processor_conf = {
    "name": "XX_Crawler.XXNewsETL.ESUploadProcessor",
    "params": {
        "es_server_list": [
            {'host': '192.168.2.21', 'port': 9200},
            {'host': '192.168.2.22', 'port': 9200},
            {'host': '192.168.2.23', 'port': 9200},
            {'host': '192.168.2.24', 'port': 9200}
        ],
        "index_name": "company_news_fulltext_v1",
        "type_name": "news"
    }
}

conf = {
    "websites":
        [
            {
                "domain_name": "中证网",
                "pipelines": [
                    {
                        "name": "公司",
                        "log_level": "debug",
                        "log_filename": "../log/zzw_ssgs.log",
                        "crawler":
                        {
                            "name": "ZZWNewsPipeline.ZZWNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://www.cs.com.cn/ssgs/",
                                "data_path": "../data/zzw/",
                                "website_name": "中证网",
                                "b_class": "公司",
                                "checkpoint_filename": "../ckpt/zzw_ssgs.ckpt",
                                "checkpoint_saved_days": 20
                                #"log_filename": "./test.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "ZZWNewsPipeline.ZZWNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },
                    {
                        "name": "市场",
                        "log_level": "info",
                        "log_filename": "../log/zzw_gppd.log",
                        "crawler":
                        {
                            "name": "ZZWNewsPipeline.ZZWNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://www.cs.com.cn/gppd/",
                                "data_path": "../data/zzw/",
                                "website_name": "中证网",
                                "b_class": "市场",
                                "checkpoint_filename": "../ckpt/zzw_gppd.ckpt",
                                "checkpoint_saved_days": 20
                                #"log_filename": "./test1.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "ZZWNewsPipeline.ZZWNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },
                    {
                        "name": "宏观",
                        "log_level": "info",
                        "log_filename": "../log/zzw_xwzx.log",
                        "crawler":
                        {
                            "name": "ZZWNewsPipeline.ZZWNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://www.cs.com.cn/xwzx/",
                                "data_path": "../data/zzw/",
                                "website_name": "中证网",
                                "b_class": "宏观",
                                "checkpoint_filename": "../ckpt/zzw_xwzx.ckpt",
                                "checkpoint_saved_days": 20
                                #"log_filename": "./test1.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "ZZWNewsPipeline.ZZWNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    }
                ]  # end of pipelines for a website
            },  # end of config of a website
            {
                "domain_name": "网易财经",
                "pipelines": [
                    {
                        "name": "首页",
                        "log_level": "info",
                        "log_filename": "../log/wy_index.log",
                        "crawler":
                        {
                            "name": "163NewsPipeline.WYNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://money.163.com/special/002557S5/newsdata_idx_index.js?callback=data_callback",
                                "data_path": "../data/163/",
                                "website_name": "网易财经",
                                "b_class": "首页",
                                "checkpoint_filename": "../ckpt/wy_index.ckpt",
                                "checkpoint_saved_days": 10
                                #"log_filename": "./test1.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "163NewsPipeline.WYNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },
                    {
                        "name": "股票",
                        "log_level": "info",
                        "log_filename": "../log/wy_stock.log",
                        "crawler":
                        {
                            "name": "163NewsPipeline.WYNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://money.163.com/special/002557S5/newsdata_idx_stock.js?callback=data_callback",
                                "data_path": "../data/163/",
                                "website_name": "网易财经",
                                "b_class": "股票",
                                "checkpoint_filename": "../ckpt/wy_stock.ckpt",
                                "checkpoint_saved_days": 10
                                #"log_filename": "./test1.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "163NewsPipeline.WYNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },
                    {
                        "name": "商业",
                        "log_level": "info",
                        "log_filename": "../log/wy_biz.log",
                        "crawler":
                        {
                            "name": "163NewsPipeline.WYNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://money.163.com/special/002557S5/newsdata_idx_biz.js?callback=data_callback",
                                "data_path": "../data/163/",
                                "website_name": "网易财经",
                                "b_class": "商业",
                                "checkpoint_filename": "../ckpt/wy_biz.ckpt",
                                "checkpoint_saved_days": 10
                                #"log_filename": "./test1.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "163NewsPipeline.WYNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },
                ]
            },  # end of wangyi 163
            {
                "domain_name": "证券时报网",
                "pipelines": [
                    {
                        "name": "快讯",
                        "log_level": "debug",
                        "log_filename": "../log/zqsb_kuaixun.log",
                        "crawler":
                        {
                            "name": "STCNNewsPipeline.STCNNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://kuaixun.stcn.com/",
                                "data_path": "../data/zqsb/",
                                "website_name": "证券时报网",
                                "b_class": "快讯",
                                "checkpoint_filename": "../ckpt/zqsb_kuaixun.ckpt",
                                "checkpoint_saved_days": 2  # 需要检查周末的情况
                                # "log_filename": "./zqsb_kuaixun.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "STCNNewsPipeline.STCNNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },  # end of pipline: stcn_kuaixun
                    {
                        "name": "股市-大盘",
                        "log_level": "debug",
                        "log_filename": "../log/zqsb_stock_dapan.log",
                        "crawler":
                        {
                            "name": "STCNNewsPipeline.STCNNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://stock.stcn.com/dapan/",
                                "data_path": "../data/zqsb/",
                                "website_name": "证券时报网",
                                "b_class": "股市",
                                "checkpoint_filename": "../ckpt/zqsb_stock_dapan.ckpt",
                                "checkpoint_saved_days": 30
                                # "log_filename": "./zqsb_stock_dapan.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "STCNNewsPipeline.STCNNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },  # end of pipline: stcn_stock_dapan
                    {
                        "name": "股市-板块个股",
                        "log_level": "debug",
                        "log_filename": "../log/zqsb_stock_bankuai.log",
                        "crawler":
                        {
                            "name": "STCNNewsPipeline.STCNNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://stock.stcn.com/bankuai/",
                                "data_path": "../data/zqsb/",
                                "website_name": "证券时报网",
                                "b_class": "股市",
                                "checkpoint_filename": "../ckpt/zqsb_stock_bankuai.ckpt",
                                "checkpoint_saved_days": 30
                                # "log_filename": "./zqsb_stock_bankuai.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "STCNNewsPipeline.STCNNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },  # end of pipline: stcn_stock_bankuai
                    {
                        "name": "股市-主力资金",
                        "log_level": "debug",
                        "log_filename": "../log/zqsb_stock_zhuli.log",
                        "crawler":
                        {
                            "name": "STCNNewsPipeline.STCNNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://stock.stcn.com/zhuli/",
                                "data_path": "../data/zqsb/",
                                "website_name": "证券时报网",
                                "b_class": "股市",
                                "checkpoint_filename": "../ckpt/zqsb_stock_zhuli.ckpt",
                                # "log_filename": "./zqsb_stock_zhuli.log"
                                "checkpoint_saved_days": 30
                            }
                        },
                        "transformers": [
                            {
                                "name": "STCNNewsPipeline.STCNNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },  # end of pipline: stcn_stock_zhuli
                    {
                        "name": "公司-新闻",
                        "log_level": "debug",
                        "log_filename": "../log/zqsb_company_gsxw.log",
                        "crawler":
                        {
                            "name": "STCNNewsPipeline.STCNNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://company.stcn.com/gsxw/",
                                "data_path": "../data/zqsb/",
                                "website_name": "证券时报网",
                                "b_class": "公司",
                                "checkpoint_filename": "../ckpt/zqsb_company_gsxw.ckpt",
                                "checkpoint_saved_days": 14
                                # "log_filename": "./zqsb_company_gsxw.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "STCNNewsPipeline.STCNNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },  # end of pipline: stcn_company_gsxw
                    {
                        "name": "公司-产经",
                        "log_level": "debug",
                        "log_filename": "../log/zqsb_company_cjnews.log",
                        "crawler":
                        {
                            "name": "STCNNewsPipeline.STCNNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://company.stcn.com/cjnews/",
                                "data_path": "../data/zqsb/",
                                "website_name": "证券时报网",
                                "b_class": "公司",
                                "checkpoint_filename": "../ckpt/zqsb_company_cjnews.ckpt",
                                "checkpoint_saved_days": 30
                                # "log_filename": "./zqsb_company_cjnews.log"
                            }
                        },
                        "transformers": [
                            {
                                "name": "STCNNewsPipeline.STCNNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    }  # , # end of pipline: stcn_company_cjnews
                ]  # end of all pipelines of 证券时报网
            },  # end of domain: 证券时报网
            {
                "domain_name": "中国证券网",
                "pipelines": [
                    {
                        "name": "公司聚焦",
                        "log_level": "debug",
                        "log_filename": "../log/zgzqw_gsxw.log",
                        "crawler":
                        {
                            "name": "ZGZQWNewsPipeline.ZGZQWNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://company.cnstock.com/company/scp_gsxw/",
                                "data_path": "../data/zgzqw/",
                                "website_name": "中国证券网",
                                "b_class": "公司聚焦",
                                "checkpoint_filename": "../ckpt/zgzqw_gsxw.ckpt",
                                "checkpoint_saved_days": 7
                            }
                        },
                        "transformers": [
                            {
                                "name": "ZGZQWNewsPipeline.ZGZQWNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    },  # end of cnstock/gsxw
                    {
                        "name": "要闻",
                        "log_level": "debug",
                        "log_filename": "../log/zgzqw_yw.log",
                        "crawler":
                        {
                            "name": "ZGZQWNewsPipeline.ZGZQWNewsCrawler",
                            "params":
                            {
                                "list_url_tpl": "http://news.cnstock.com/news/sns_yw/",
                                "data_path": "../data/zgzqw/",
                                "website_name": "中国证券网",
                                "b_class": "要闻",
                                "checkpoint_filename": "../ckpt/zgzqw_yw.ckpt",
                                "checkpoint_saved_days": 7
                            }
                        },
                        "transformers": [
                            {
                                "name": "ZGZQWNewsPipeline.ZGZQWNewsContentParser",
                                "params": {}
                            },
                            es_uploader_processor_conf,
                        ],
                        "uploader": es_uploader_conf
                    }  # end of cnstock/yw
                ]  # end of piplines of 中国证券网
            }  # end of domain: 中国证券网
        ]  # end of the list of websites
}
