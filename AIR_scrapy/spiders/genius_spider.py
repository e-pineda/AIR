# -*- coding: utf-8 -*-
import scrapy
import time
from selenium import webdriver
from bs4 import BeautifulSoup
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.WARNING)


available_sections = ['skit', 'intro', 'verse', 'pre_chorus', 'chorus', 'post_chorus', 'ad_libs', 'bridge',
                      'interlude', 'outro']

class SongItem(scrapy.Item):
    artist = scrapy.Field()
    title = scrapy.Field()
    intro = scrapy.Field()
    verse = scrapy.Field()
    pre_chorus = scrapy.Field()
    chorus = scrapy.Field()
    post_chorus = scrapy.Field()
    bridge = scrapy.Field()
    ad_libs = scrapy.Field()
    interlude = scrapy.Field()
    outro = scrapy.Field()
    skit = scrapy.Field()


class AirSpider(scrapy.Spider):
    name = "genius"

    def __init__(self):
        # get list of rapppers
        self.rapper_list = []
        self.get_rapper_list()

        # amount of songs to scrape by each artist
        self.song_amount = 200

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
        og_url = 'https://genius.com/artists/'
        for artist in self.rapper_list:
            print('Scraping:', artist)
            yield scrapy.Request(url=og_url+artist, callback=self.parse, meta={'artist_name': artist})

    def parse(self, response):
        self.driver.get(response.url)
        loop_flag = True
        artist_name = response.meta.get('artist_name')

        # Prepares the page to be scraped
        while loop_flag:

            # Show all songs by the artist
            self.show_all_songs()

            # Get all 150 songs barring duplicates and songs that the artist isnt spitting shit for
            lyrics = self.get_songs(artist_name)
            print('AMOUNT OF SONGS:', len(lyrics), len(set(lyrics)))

            # Get lyrics for each of the songs
            for counter, lyric_link in enumerate(lyrics):
                print('On link number ', counter, lyric_link)
                yield scrapy.Request(lyric_link, callback=self.parse_song, meta={'artist_name': artist_name,
                                                                                 'link': lyric_link})
            loop_flag = False

        # self.driver.close()

    # read in list of rappers
    def get_rapper_list(self):
        with open('rapper_list.txt', 'r') as infile:
            for line in infile:
                self.rapper_list.append(line.strip())
        infile.close()
        return self.rapper_list

    # show all songs and wait
    def show_all_songs(self):
        self.driver.find_element_by_css_selector('div[class="full_width_button u-clickable u-bottom_margin"]').click()
        time.sleep(5)

    # get all songs
    def get_songs(self, artist):
        max_tries = 45
        curr_try = 0
        lyric_urls = set()

        # enter artist name in the text field first
        # input_element = self.driver.find_elements_by_css_selector('input[type="text"]')[1]
        # input_element.send_keys(artist)
        # time.sleep(5)

        # get links to the articles
        while len(lyric_urls) < self.song_amount and curr_try < max_tries:
            song_elements = self.driver.find_elements_by_css_selector('a[class="mini_card mini_card--small')
            for song in song_elements:
                lyric_urls.add(song.get_attribute('href'))
            song.location_once_scrolled_into_view
            print('TRY BITCH', curr_try, max_tries, curr_try<max_tries)
            curr_try += 1
        return lyric_urls

    def correct_section_names(self, section_name, artist_name):
        if 'hook' in section_name or 'chorus' in section_name:
            return 'chorus'
        elif 'verse' in section_name or artist_name in section_name.lower().replace(' ','') or 'verso' in section_name \
                or 'beat' in section_name:
            return 'verse'
        elif "pre-chorus" in section_name:
            return 'pre_chorus'
        elif 'post-chorus' in section_name:
            return 'post_chorus'
        elif 'ad-libs' in section_name or 'adlib' in section_name:
            return 'ad_libs'
        elif 'interlude' in section_name:
            return 'interlude'
        elif 'intro' in section_name:
            return 'intro'
        elif 'outro' in section_name:
            return 'outro'
        elif 'skit' in section_name:
            return 'skit'
        elif 'bridge' in section_name:
            return 'bridge'
        else:
            return section_name

    def is_section_name(self, possible_section, artist):
        possible_section = self.correct_section_names(possible_section, artist)
        if possible_section not in available_sections:
            return False
        return True

    def parse_song(self, response):
        song = SongItem()
        song['artist'] = response.meta.get('artist_name')
        song['title'] = response.css('h1.header_with_cover_art-primary_info-title::text').extract()[0]
        song['intro'] = ''
        song['verse'] = ''
        song['pre_chorus'] = ''
        song['chorus'] = ''
        song['post_chorus'] = ''
        song['ad_libs'] = ''
        song['bridge'] = ''
        song['interlude'] = ''
        song['outro'] = ''
        song['skit'] = ''

        # use beautifulsoup to scrape lyrics
        soup = BeautifulSoup(response.text, 'html.parser')
        lyrics = soup.find("div", class_="lyrics").get_text()
        song = self.separate_lyrics(lyrics, song, response.meta.get('artist_name'))

        yield song

    def separate_lyrics(self, lyrics, song, artist):
        sections = self.clean_lyrics(lyrics.split('\n'), artist)
        section_name = ''
        record_bar_flag = False
        # print(sections)

        for section in sections:
            # if the bar is empty or the producer tag
            if section == '' or '[Produced ' in section:
                continue

            # check what section we're working with and if its by the given artist
            elif '[' in section:
                section = section.replace('[', '').replace(']', '').strip()

                # check if the section is by the artist
                if ':' in section:
                    who_this = section.split(':')[1].strip()

                    if who_this == artist or artist in who_this:
                       record_bar_flag = True
                       section_name = self.correct_section_names(section_name=section.split(':')[0].lower(),
                                                                 artist_name=artist)

                    else:
                        record_bar_flag = False

                # if there's no colon, we know its by the artist
                else:
                    record_bar_flag = True
                    section_name = self.correct_section_names(section_name=section.split(':')[0].lower(),
                                                              artist_name=artist.lower().replace(' ',''))

            elif record_bar_flag:

                # adlibs
                if '(' in section or ')' in section:
                    adlibs, section = self.find_adlibs(section)
                    song['ad_libs'] += adlibs
                    if section == '':
                        continue

                song[section_name] += section + '\n'

        return song

    def find_adlibs(self, bar):
        adlibs = ''

        adlib_start_positions = self.find_occurrences('(', bar)
        adlib_end_positions = self.find_occurrences(')', bar)

        if len(adlib_end_positions) == 0:
            adlib = bar[adlib_start_positions[0] + 1:]
            bar = bar.replace(bar[adlib_start_positions[0]:], '')
            adlibs += adlib + '\n'
            return adlibs, bar

        elif len(adlib_start_positions) == 0:
            adlib = bar[:adlib_end_positions[0] + 1]
            bar = bar.replace(bar[:adlib_end_positions[0]], '')
            adlibs += adlib + '\n'
            return adlibs, bar

        for adlib_start, adlib_end in zip(adlib_start_positions, adlib_end_positions):
            adlib = bar[adlib_start + 1:adlib_end]
            bar = bar.replace(bar[adlib_start:adlib_end + 1], '')
            # print(adlib, '||||||', bar)
            adlibs += adlib + '\n'

        return adlibs, bar

    def find_occurrences(self, character, bar):
        return [i for i, letter in enumerate(bar) if letter == character]

    def clean_lyrics(self, lyrics, artist):
        cleaned_lyrics = []
        for bar in lyrics:
            if '[' in bar:
                possible_section = bar[bar.find('[')+1:bar.find(']')].split(':')[0].lower().replace(' ','')
                if not self.is_section_name(possible_section, artist.lower().replace(' ','')):
                    print('FAKE ASS SECTION DETECTED', possible_section)
                    continue
            cleaned_lyrics.append(bar)
        return cleaned_lyrics

# take out breaks, non-stop, [?], skit