# -*- coding: utf-8 -*-

############################################
##
# run all pipelines in conf file
##
##
#############################################


from XX_Crawler.XXNewsETL import *
from XX_Crawler.Utils import *
from NewsPipelineConf import conf


if __name__ == "__main__":
    npl = NewsPipeline(conf)
    npl.run()
