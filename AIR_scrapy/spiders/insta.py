# -*- coding: utf-8 -*-
import scrapy
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import sys
import logging
import os
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class InstaSpider(scrapy.Spider):
    name = 'insta'
    allowed_domains = ['instagram.com']
    start_urls = ['http://instagram.com/']

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse)

    def parse(self, response):
        self.driver.get(response.url)