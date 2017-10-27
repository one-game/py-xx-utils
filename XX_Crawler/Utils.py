# -*- coding: utf-8 -*-

############################################
##
# defination of new crawler framework
##
##
#############################################

import sys
import traceback
import logging
import time
from logging.handlers import TimedRotatingFileHandler


def import_class(import_str):
    """Returns a class from a string including module and class.
    .. versionadded:: 0.3
    """
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)
    try:
        return getattr(sys.modules[mod_str], class_str)
    except AttributeError:
        raise ImportError('Class %s cannot be found (%s)' %
                          (class_str,
                           traceback.format_exception(*sys.exc_info())))


def import_object(import_str, kwargs):
    """Import a class and return an instance of it.
    .. versionadded:: 0.3
    """
    return import_class(import_str)(**kwargs)


def get(url,
        timeout=30,
        header={},
        max_request_retry=3,
        requests_interval=1,
        exception_interval=1,
        banned_interval=60,
        is_page_banned=lambda x: False
        ):
    retry_count = 0
    while retry_count < max_request_retry:
        try:
            retry_count += 1
            logging.debug("getting " + url)
            page = requests.get(url, timeout=timeout, headers=header)
            if page.status_code != 200:
                logging.warning("url:%s return %d" % (url, page.status_code))
                return None
            if not is_page_banned(page.content):
                time.sleep(requests_interval)
                #self.doc_counter += 1
                return page.content
            else:
                time.sleep(banned_interval)
        except Exception as e:
            logging.debug("get exception : " + str(e))
            time.sleep(exception_interval)
    return None


LEVELS = {
          'notset': logging.DEBUG,
          'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL
          }


def InitLog(filename, logger, level):
    # handler = logging.handlers.RotatingFileHandler(
    #     LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=LOG_BACKUPCOUNT)
    handler = logging.FileHandler(filename)
    # handler = TimedRotatingFileHandler(filename,
    #                                    when='d',
    #                                    interval=1,
    #                                    backupCount=7)
    formatter = logging.Formatter(
        '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s==>%(message)s')
    handler.setFormatter(formatter)
    #logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(LEVELS.get(level.lower()))
    logger.propagate = False
    return logger
