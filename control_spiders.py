from pathlib import Path

import pandas as pd
from scrapy import cmdline
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from selenium import webdriver

import sys
sys.path.insert(0, 'AIR_scrapy/spiders/')
from AIR_scrapy.spiders import genius_spiders


class SpiderControl(object):
    def __init__(self):
        self.url_file_path = 'Prod Serialized Link Scrape'
        self.lyric_file_path = 'Prod Serialized Lyric Scrape'
        # self.rapper_list_file_path = 'test_rappers.txt'  #for testing
        self.rapper_list_file_path = 'rapper_list.txt'

        self.artist_col, self.link_col = [], []
        self.lyric_col, self.song_title_col, self.features_col = [], [], []
        self.starting_lyric_position = 0
         
        self.launch_url_flag, self.launch_lyric_flag = False, False

        # get list of rappers from inputted documents
        self.rapper_list = self.get_rapper_list(self.rapper_list_file_path)
        self.link_rapper_list, self.lyric_rapper_list = self.rapper_list, self.rapper_list
        self.webdriver_options = self.initialize_chrome_settings()

    # check if file exists
    @staticmethod
    def file_exists(f_path):
        serialized_file = Path(f_path)
        if serialized_file.is_file():
            return True
        return False

    # read in list of rappers
    @staticmethod
    def get_rapper_list(fpath):
        rapper_list = []
        with open(fpath, 'r', encoding='utf-8') as infile:
            for line in infile:
                rapper_list.append(line.strip())
        infile.close()
        return rapper_list

    # updates rapper list
    @staticmethod
    def update_rapper_list(rap_list, df, key_col):
        scraped_artists = set(df['Artist'].tolist())
        unfinished_artists = set(df[df[key_col] == "Unfinished"]['Artist'].values)

        # finished artists = scraped artists - unfinished artists
        # all artists that need to be rescraped or scraped will be left by rap_list - finished_artists
        remaining_artists_links = set(rap_list) - (scraped_artists - unfinished_artists)

        return list(remaining_artists_links)

    @staticmethod
    def initialize_chrome_settings():
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--log-level=2")
        chrome_options.add_argument("--log-level=1")
        chrome_options.add_argument("--log-level=0")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-login-animations")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-default-apps")
        return chrome_options

    def should_launch_url_spider(self):
        if self.file_exists(self.url_file_path):
            df = pd.read_csv(self.url_file_path, index_col=[0]).astype(str)

            # update rapper list to get remainder of artists
            self.link_rapper_list = self.update_rapper_list(self.rapper_list, df, key_col='Link')

            # rappers need to be scraped
            if len(self.link_rapper_list) > 0:
                print('Need to scrape rappers for links:', self.link_rapper_list)
                self.launch_url_flag = True
            else:
                print("Don't need to scrape any rappers for song links")
        else:
            self.launch_url_flag = True
            print('You dont have anything for links! Should launch url spider to get links')
        return self.launch_url_flag

    def prepare_url_spider(self):
        if self.file_exists(self.url_file_path):
            df = pd.read_csv(self.url_file_path, index_col=[0]).astype(str)

            # remove all rows that are unfinished
            rows_to_be_dropped = df[df['Link'] == "Unfinished"]['Artist'].index
            df.drop(rows_to_be_dropped, inplace=True)
            print('Dropped', len(rows_to_be_dropped), 'rows')

            # reset tracking lists that will be used as dataframe columns
            self.artist_col, self.link_col = list(df["Artist"]), list(df["Link"])
        else: #otherwise, there is no file to read from and have to initalize the tracking lists
            self.artist_col, self.link_col = [], []
            self.lyric_col, self.song_title_col, self.features_col = [], [], []

        print('Prepared to launch URL spider')

    def launch_url_spider(self):
        # Launch spider to scrape urls -- spider serializes and creates Serialized Link Scrape.csv
        print('Launching URL Spider')
        process = CrawlerProcess(get_project_settings())
        process.crawl(genius_spiders.UrlSpider, rapper_list=self.link_rapper_list, artists=self.artist_col,
                      links=self.link_col, options=self.webdriver_options, serialized_fname=self.url_file_path)
        process.start()
        print('Finished Launch of URL Spider')

    def should_launch_lyric_spider(self):
        # if we need to resume link scraping, then start now
        if self.file_exists(self.lyric_file_path):
            df = pd.read_csv(self.lyric_file_path, index_col=[0]).astype(str)

            # update rapper list to get remainder of artists
            self.lyric_rapper_list = self.update_rapper_list(self.lyric_rapper_list, df, key_col='Lyrics')

            if len(self.lyric_rapper_list) > 0:
                print('Need to scrape rappers for lyrics:', self.lyric_rapper_list)
                self.launch_lyric_flag = True
            else:
                print('Dont need to scrape any lyrics')
        else:
            self.launch_lyric_flag = True
            print('You dont have anything for lyrics! Should launch lyric spider to get lyrics')

        return self.launch_lyric_flag

    def prepare_lyric_spider(self):

        # resume a previous scrape sesh
        if self.file_exists(self.lyric_file_path):
            df = pd.read_csv(self.lyric_file_path, index_col=[0]).astype(str)

            rows_to_be_dropped = df[df['Lyrics'] == "Unfinished"]['Artist'].index
            df.drop(rows_to_be_dropped, inplace=True)
            print('Dropped', len(rows_to_be_dropped), 'rows')

            starting_row = df[df['Lyrics'] == 'nan']['Artist'].index[0]
            self.starting_lyric_position = starting_row

            self.artist_col, self.link_col = list(df['Artist']), list(df['Link'])
            self.lyric_col, self.song_title_col, self.features_col = list(df["Lyrics"]), list(df["Song Title"]), list(df["Features"])
            wait = input('Finna start scraping lyrics starting from row ' + str(self.starting_lyric_position) + '...')

        # no prior scrape sesh exists, start a new one -- a url scrape sesh must be completed first!
        else:
            try:
                df = pd.read_csv(self.url_file_path, index_col=[0]).astype(str)
                self.artist_col, self.link_col = list(df['Artist']), list(df['Link'])
                self.lyric_col, self.song_title_col, self.features_col = list(df["Lyrics"]), list(
                    df["Song Title"]), list(
                    df["Features"])
                print('Prepared to launch lyric spider')

            except FileNotFoundError as e:
                print("MISSING A URL SCRAPE SESH, your headass needs that\ncant launch the Lyric Spider")
                return e

    def launch_lyric_spider(self):
        # Launch spider to scrape urls -- spider serializes and creates Serialized Link Scrape.csv
        print('Launching Lyric Spider')
        process = CrawlerProcess(get_project_settings())
        process.crawl(genius_spiders.LyricSpider, starting_pos=self.starting_lyric_position,
                      options=self.webdriver_options, serialized_fname=self.lyric_file_path, urls=self.link_col,
                      artists=self.artist_col, lyrics=self.lyric_col, titles=self.song_title_col, features=self.features_col)
        process.start()
        print('Finished Launch of URL Spider')


s_control = SpiderControl()
if s_control.should_launch_url_spider():
    s_control.prepare_url_spider()
    s_control.launch_url_spider()

elif s_control.should_launch_lyric_spider():
    potential_error = s_control.prepare_lyric_spider()
    if potential_error is None:
        s_control.launch_lyric_spider()


# cmdline.execute("scrapy crawl genius".split())
# cmdline.execute("scrapy crawl bpm".split())
