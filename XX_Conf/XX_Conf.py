#coding=utf-8
##############################################################
## 
## Parse config file whose format likes key=value
## And province config data like a dict
##
## Author: zhang xiang
## Date : 2017/3/20
##
##############################################################

class XX_Conf:
    """
    配置类
    """
    _data = {}
    
    def __init__(self, conf_path):
        """
        初始化配置，入参为配置路径
        """
        with open(conf_path, "r") as fd:
            lines = fd.readlines()
            for line in lines:
                key, value = line.strip("\n ").split("=")
                self._data[key.strip(" ")] = value.strip(" ")
            fd.close()
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def __getitem__(self, key):
        return self._data[key]
            
    