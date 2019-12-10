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
small_delay = 2
delay = 7
long_delay = 60


class BpmSpider(scrapy.Spider):
    name = 'bpm'
    allowed_domains = ['https://songbpm.com/']
    start_urls = ['http://songbpm.com/']

    def __init__(self):
        # get bpms
        self.rapper_info_df = pd.read_csv('rapper_scrape.csv')


        # initaite webdriver
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
        self.driver = webdriver.Chrome(chrome_options=chrome_options)

    def start_requests(self):
        og_url = 'http://songbpm.com/'
        yield scrapy.Request(url=og_url, callback=self.parse)

    def parse(self, response):
        self.driver.get(response.url)
        rappers = self.rapper_info_df['artist'].tolist()
        songs = self.rapper_info_df['title'].tolist()
        try:
            bpm_df = pd.read_csv('bpms.csv')
            bpm_list = bpm_df['BPM'].tolist()
        except Exception as e:
            bpm_list = ['YEEHAW' for i in range(len(songs))]
            bpm_df = pd.DataFrame(columns=['Rappers', 'Songs', 'BPM'])
            bpm_df["Rappers"] = rappers
            bpm_df['Songs'] = [song.replace(',', '') for song in songs]

        print(bpm_list)
        old_url = None
        old_matches = None
        max_tries = 3

        counter = 0
        for rapper, song_title, bpm in zip(rappers, songs, bpm_list):
            try:
                if bpm != 'YEEHAW':
                    print('BPM PASSED', bpm, counter)
                    counter += 1
                    continue
                print('BPM CHECK', bpm, counter)
                # enter artist and song info in the text box
                self.enter_info(rapper, song_title)

                # get results from search
                possible_matches = self.driver.find_elements_by_css_selector('a[class="media"]')

                # if page doesn't load, refresh and shit
                tries = 0
                while self.driver.current_url == old_url or possible_matches == old_matches:
                    possible_matches = self.driver.find_elements_by_css_selector('a[class="media"]')
                    if self.driver.current_url == old_url:
                        self.enter_info(rapper, song_title)

                    elif tries <= 2:
                        self.driver.refresh()

                    tries += 1
                    if tries == max_tries:
                        break

                time.sleep(small_delay)

                possible_matches = self.driver.find_elements_by_css_selector('a[class="media"]')
                old_url = self.driver.current_url
                old_matches = possible_matches

                # if there are no results from search
                if len(possible_matches) == 0:
                    print('NO MATCHES FOR SONG ', song_title, ' PROGRESS: ', round(((counter/len(songs))*100), 3), '%')
                    bpm = 'BOOKMARKED'

                else:
                    # if match, record bpm and continue
                    bpm = self.find_match(possible_matches, rapper, song_title)
                    print('SONG: ', song_title, ' SELECTED BPM :', bpm, ' PROGRESS: ', round(((counter/len(songs))*100),
                                                                                             3), '%')

                bpm_list[counter] = bpm
                if counter % 25 == 0:
                    self.cerealize(bpm_df=bpm_df, bpm_list=bpm_list)

                counter += 1
                print('-------------------------------')

            except Exception as e:
                print(e)
                self.cerealize(bpm_df=bpm_df, bpm_list=bpm_list)
                sys.exit()

        self.cerealize(bpm_df=bpm_df, bpm_list=bpm_list)
        sys.exit()

    def find_match(self, possible_matches, og_artist, og_song_title):
        near_matches = []

        if '’' in og_song_title:
            og_song_title = og_song_title.replace('’', '')

        for match in possible_matches:
            artist_name, song_name, bpm = self.get_match_info(match)

            if "'" in song_name:
                song_name = song_name.replace("'", '')

            # if len(near_matches) == 0:
            #     print('hit the woah')
            #     print(og_song_title.lower(), song_name.lower())

            # perfect match
            if og_artist.lower() == artist_name.lower().strip() and og_song_title.lower() == song_name.lower().strip():
                return bpm

            # if artist name is not in the artist section and the artist isnt in the song title and the ogsong_title
            # isnt in the song title, then skip
            elif og_artist.lower() not in artist_name.lower().strip() and og_artist.lower() not in \
                    song_name.lower().strip() and og_song_title.lower() not in song_name.lower().strip():
                continue

            # if the song names match up or the artist is in the song's description
            elif og_song_title.lower() in song_name.lower() or og_artist.lower() in artist_name.lower() or \
                    og_artist.lower() in song_name.lower():
                near_matches.append(match)

        # reduce near_matches
        near_matches = self.reduce_matches_by_bpm(near_matches)
        print('LENGTH OF NEAR MATCHES', len(near_matches))
        if len(near_matches) >= 3:
            near_matches = self.reduce_matches_by_artist(near_matches, og_artist)
            print('UPDATED LENGTH OF NEAR MATCHES', len(near_matches))

        # if there's one match
        if len(near_matches) == 1:
            artist_name, song_name, bpm = self.get_match_info(near_matches[0])
            return bpm

        # if there's two matches
        if len(near_matches) == 2:
            artist_name, song_name, bpm_1 = self.get_match_info(near_matches[0])
            artist_name, song_name, bpm_2 = self.get_match_info(near_matches[1])
            return min(int(bpm_1), int(bpm_2))

        return 'BOOKMARKED'

    def reduce_matches_by_bpm(self, possible_matches):
        bpm_set = set()
        remaining_matches = []
        for match in possible_matches:
            artist_name, song_name, bpm = self.get_match_info(match)
            if bpm not in bpm_set:
               bpm_set.add(bpm)
               remaining_matches.append(match)
            else:
                continue
        return remaining_matches

    def reduce_matches_by_artist(self, possible_matches, og_artist):
        remaining_matches = []
        for match in possible_matches:
            artist_name, song_name, bpm = self.get_match_info(match)

            if og_artist.lower() not in artist_name.lower().strip() and og_artist.lower() not in song_name.lower().strip():
                continue
            elif og_artist.lower() in artist_name.lower().strip() or og_artist.lower() in song_name.lower().strip():
                remaining_matches.append(match)

        return remaining_matches

    def get_match_info(self, match):
        try:
            artist_name = match.find_element_by_css_selector('p[class="subtitle is-6 artist-name"').text.lower()
            song_name = match.find_element_by_css_selector('p[class="title is-4 track-name"').text.lower()
            bpm = match.find_elements_by_css_selector('p[class="title"')[1].text
        except Exception as e:
            self.driver.refresh()
            artist_name = match.find_element_by_css_selector('p[class="subtitle is-6 artist-name"').text.lower()
            song_name = match.find_element_by_css_selector('p[class="title is-4 track-name"').text.lower()
            bpm = match.find_elements_by_css_selector('p[class="title"')[1].text
        return artist_name, song_name, bpm

    def enter_info(self, rapper, song):
        # enter artist name in the text field first
        try:
            input_element = self.driver.find_element_by_css_selector('input[type="text"]')
        except Exception as e:
            self.driver.refresh()
            input_element = self.driver.find_element_by_css_selector('input[type="text"]')
        # clears text box of any recent searches
        input_element.send_keys(Keys.CONTROL + "a")
        input_element.send_keys(Keys.DELETE)

        # searches for given song and artist
        input_element.send_keys(rapper + ' ' + song)
        input_element.send_keys(Keys.RETURN)
        # self.driver.refresh()

    def wait(self):
        self.driver.refresh()
        time.sleep(delay)

    def cerealize(self, bpm_df, bpm_list):
        bpm_df['BPM'] = bpm_list
        bpm_df.to_csv('bpms.csv', index=False)

        # READ BPMS
        bpm_df = pd.read_csv('bpms.csv')

        # READ SONG INFO
        song_df = pd.read_csv('rapper_scrape.csv')

        # ADD BPMS TO SONG_INFO DF
        song_df['bpm'] = bpm_df['BPM']

        # SORT DATAFRAME BY ARTIST NAME, THEN BY SONG NAME
        temp_df = song_df.sort_values(['artist', 'title'], ascending=[True, True])

        # SAVE VALUE
        temp_df.to_csv('final_info.csv', index=False)
        print('CEREALIZED BABY')
