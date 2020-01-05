import time

import pandas as pd
import scrapy
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider
from selenium import webdriver


class UrlSpider(scrapy.Spider):
    name = "UrlSpider"

    def __init__(self, rapper_list, artists, links, options, serialized_fname):
        self.urls, self.artists, self.rapper_list = links, artists, rapper_list
        self.avail_columns = ['Artist', 'Link']
        self.df_cols = ['Artist', 'Link', 'Song Title', 'Features', 'Producers', 'Lyrics']
        self.bot_sleep_time = 3
        self.dataframe = []

        self.lyric_col, self.song_title_col, self.features_col = [], [], []
        self.serialized_fname = serialized_fname

        self.driver = webdriver.Chrome(chrome_options=options)

    def gen_empty_lists(self, count):
        remaining_cols = [col for col in self.df_cols if col not in self.avail_columns]
        empty_lists = [[None for i in range(count)] for i in range(len(remaining_cols))]
        return remaining_cols, empty_lists

    def start_requests(self):
        #loop through every artist and get links to every song --will serialize links to csv if spider fails
        for artist in self.rapper_list:
            print('Scraping:', artist)
            yield scrapy.Request(url='https://genius.com/artists/' + artist, callback=self.parse_urls,
                                 meta={'artist_name': artist})

    def parse_urls(self, response):
        artist_name = response.meta.get('artist_name')
        try:
            self.driver.get(response.url)

            # Show all songs by the artist
            self.driver.find_element_by_css_selector(
                'div[class="full_width_button u-clickable u-bottom_margin"]').click()
            time.sleep(self.bot_sleep_time)

            # search the artist by name
            sbox = self.driver.find_element_by_css_selector('div.square_input_and_icon input[type="text"]')
            sbox.send_keys(artist_name)
            time.sleep(self.bot_sleep_time)

            # Get all songs barring duplicates and songs that the artist isnt spitting shit for
            urls, error = self.get_songs()

            og_length = len(self.urls)
            self.urls.extend(urls)
            url_set_length = len(self.urls)
            self.artists.extend([artist_name for i in range(url_set_length - og_length)])

            self.serialize_urls(error, errored_artist=artist_name)

        except Exception as error:
            print('caught the error')
            self.serialize_urls(error, errored_artist=artist_name)
            print('There was an error, boutta dip outta here')
            raise CloseSpider(error)

    # get all songs
    def get_songs(self):
        lyric_url_set = set()

        # get amount of results to know when to sop scrolling
        s_results = self.driver.find_element_by_css_selector('div[class="profile_list_item profile_list_item--large_padding"]').text
        s_results = int(s_results.split()[0])
        print("DIFFERENT RESULTS", s_results)

        max_tries = 3
        curr_try = 0
        last_lyrics_urls = 0

        # get links to the articles
        try:
            while curr_try < max_tries:
                time.sleep(2)
                song_elements = self.driver.find_elements_by_css_selector('a[class="mini_card mini_card--small"]')

                for song in song_elements:
                    lyric_url_set.add(song.get_attribute('href'))

                song.location_once_scrolled_into_view
                # print("LYRIC URLS GATHERED: ", len(lyric_url_set), " RESULTS: ", str(s_results))

                if last_lyrics_urls == len(lyric_url_set):
                    curr_try += 1
                else:
                    last_lyrics_urls = len(lyric_url_set)
                    curr_try = 0

                if curr_try >= 3:
                    print("Current try: ", curr_try, " Max Try: ", max_tries)
            return list(lyric_url_set), None

        except Exception as e:
            print("ERRORED AT GET_SONGS FUNCTION")
            return list(lyric_url_set), e

    def serialize_urls(self, error, errored_artist=None):
        if error:
            print("APPENDED IN SERIALIZED FUNCTION")
            self.urls.append('Unfinished'), self.artists.append(errored_artist)
            print('LENGTH OF URLS', len(self.urls))

        other_cols, empty_lists = self.gen_empty_lists(len(self.urls))

        df_values = dict(zip(other_cols, empty_lists))
        df_values['Link'], df_values['Artist'] = self.urls, self.artists

        print('SERIALIZED')
        self.dataframe = pd.DataFrame(df_values)
        self.dataframe.drop_duplicates(subset=['Link', 'Artist'], keep='first', inplace=True)
        self.dataframe.to_csv(self.serialized_fname)


class LyricSpider(scrapy.Spider):
    name = 'LyricSpider'

    def __init__(self, urls, artists, lyrics, titles, features, starting_pos, options, serialized_fname):
        self.urls, self.artists = urls, artists
        self.lyric_col, self.song_title_col, self.features_col = lyrics, titles, features

        self.bot_sleep_time = 3

        self.starting_pos = starting_pos
        self.serialized_fname = serialized_fname

    def start_requests(self):
        # get lyrics for song urls scraped above
        for link in self.urls[self.starting_pos:]:  #begin at the first row with a nan
            artist_name = self.artists[self.starting_pos]
            print(artist_name, 'Currently on song', self.starting_pos, 'out of', len(self.urls))
            yield scrapy.Request(url=link, callback=self.parse_lyrics, meta={'index': self.starting_pos,
                                                                             'artist_name': artist_name})
            self.starting_pos += 1

    def parse_lyrics(self, response):
        artist_name = response.meta.get('artist_name')
        counter = response.meta.get('index')
        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            lyrics = soup.find("div", class_="song_body-lyrics").get_text().strip()
            title = soup.find('h1', class_='header_with_cover_art-primary_info-title').get_text().strip()

            # will take who it is written by
            song_info = soup.find('div', class_='u-xx_large_vertical_margins show_tiny_edit_button_on_hover')
            features = song_info.find("span", class_='metadata_unit-info').get_text().strip()

            self.lyric_col[counter] = lyrics
            self.song_title_col[counter] = title
            self.features_col[counter] = features
            self.serialize_lyrics()

        except AttributeError as e:
            self.lyric_col[counter] = 'Unscrapable'
            self.song_title_col[counter] = None
            self.features_col[counter] = None

        except Exception as e:
            self.lyric_col.append('Unfinished'), self.features_col.append(None), self.song_title_col.append(None)
            self.artists.append(artist_name), self.urls.append(None)
            self.serialize_lyrics(error=e)
            print('boutta dip')
            raise CloseSpider(e)

    # serializes file
    def serialize_lyrics(self, error=None):
        df_values = {'Artist': self.artists, 'Link': self.urls, 'Features': self.features_col,
                     'Song Title': self.song_title_col, 'Lyrics': self.lyric_col}

        df = pd.DataFrame(df_values)
        df.to_csv(self.serialized_fname)
