import pandas as pd
pd.set_option('display.max_columns', 30)
pd.options.mode.chained_assignment = None


class RangeError(LookupError):
    '''raise this when there's a lookup error for my app'''


class UserInterface(object):
    def __init__(self):
        self.df = pd.read_csv('final_info.csv')

        self.categories = self.df.columns.tolist()

        # Get song sections
        self.selectable_parts = self.categories
        self.selectable_parts.remove('bpm')
        self.selectable_parts.remove('title')
        self.selectable_parts.remove('artist')

        self.artist_amount = 5

        self.temp_df = None
        self.temp_artists = []
        self.temp_section = ''
        self.abs_min_bpm = None
        self.abs_max_bpm = None


    def choose_training_method(self):
        corr_answers = ['bpm', 'artist', 'both']
        print('Would you like to train by (bpm), (artist) or (both)?')
        ans = input('Answer here: ')
        while ans not in corr_answers:
            ans = input('Answer here: ')
        return ans

    def select_song_section(self):
        print('Below are song sections that you can choose')
        print(self.selectable_parts)
        section = input('Pick a section: ')
        while section not in self.selectable_parts:
            section = input('Pick a section: ')
        self.temp_section = section
        self.load_available_data()
        return section

    def load_available_data(self):
        self.temp_df = self.df.loc[(self.df[self.temp_section].notnull())]
        self.temp_df.bpm = pd.to_numeric(self.temp_df.bpm, errors='coerce').fillna(0).astype(int)

        # self.temp_df = self.df.loc[(self.df[self.temp_section].notnull()) & (self.df['bpm'] != 'BOOKMARKED') &
        #                            (self.df['bpm'] != '0')]
        # self.temp_df.bpm = self.temp_df['bpm'].astype(int)

    # loads available artists, prompts the user for their artists choice and then return the appropiate data
    def select_artists(self):
        # load available artists
        self.load_available_artists()

        # get users's artists
        selected_artists = self.get_artists()

        # Get dataframe with appropiate data
        self.temp_df = self.temp_df.loc[self.temp_df['artist'].isin(selected_artists)]
        appropiate_df = self.temp_df[['artist', 'title', self.temp_section]]
        return appropiate_df

    def get_artists(self):
        # prompts user for their artists selection
        print('\nPlease select', str(self.artist_amount), 'artists from below')
        print(self.temp_artists)
        selected_artists = []
        for i in range(1, self.artist_amount+1):
            artist = input('Pick artist ' + str(i) + ': ')
            while artist not in self.temp_artists:
                artist = input('Pick artist ' + str(i) + ': ')
            selected_artists.append(artist)
        return selected_artists

    # load available artists for the user to select artists
    def load_available_artists(self):
        self.temp_artists = list(sorted(set(self.temp_df['artist'].tolist())))

    # prompts user for their bpm-range and returns the appropiate data
    def select_bpm(self):
        # show range of bpms
        self.load_bpm_range()

        # get bpm range
        min = self.get_bpm('min')
        max = self.get_bpm('max')

        # get values within bpm range from temp_df
        self.temp_df = self.temp_df[(self.temp_df['bpm'] >= min) & (self.temp_df['bpm'] <= max)]

        # return dataframe with relevant info
        appropiate_df = self.temp_df[['artist', 'title', 'bpm', self.temp_section]]
        return appropiate_df

    def load_bpm_range(self):
        self.abs_min_bpm = self.temp_df['bpm'].min()
        self.abs_max_bpm = self.temp_df['bpm'].max()

        print("The minimum bpm you can enter is: ", self.abs_min_bpm)
        print("The maximum bpm you can enter is: ", self.abs_max_bpm)

    # get range of bpms
    def get_bpm(self, end):
        bpm = 0
        for i in range(100):
            while True:
                try:
                    bpm = int(input('Enter the ' + end + ' of the bpm-range: '))
                    if bpm > self.abs_max_bpm or bpm < self.abs_min_bpm:
                        raise RangeError('Your input was outside of the bpm limits')
                except (ValueError, RangeError):
                    continue
                break
            return bpm

    # prompts user for artists and bpm-range, then acquires appropriate data
    def select_both(self):
        # load available artists
        self.load_available_artists()

        # get users's artists
        selected_artists = self.get_artists()

        # Get dataframe with appropiate artist data
        self.temp_df = self.temp_df.loc[self.temp_df['artist'].isin(selected_artists)]

        # show range of bpms
        self.load_bpm_range()

        # get bpm range
        min = self.get_bpm('min')
        max = self.get_bpm('max')

        # Get dataframe with appropiate bpm data
        self.temp_df = self.temp_df[(self.temp_df['bpm'] >= min) & (self.temp_df['bpm'] <= max)]

        appropiate_df = self.temp_df[['artist', 'title', 'bpm', self.temp_section]]
        return appropiate_df


def interface():
    ui = UserInterface()

    # get song section and load available data
    section = ui.select_song_section()

    # choose training_method
    choice = ui.choose_training_method()

    # if artist, then continue to ui.select_artists()
    if choice == 'artist':
        dataframe = ui.select_artists()
        # print(dataframe)
        print('There are', len(set(dataframe['artist'].tolist())), 'artists. These artists are:',
              set(dataframe['artist'].tolist()), 'with a total of', len(dataframe[section].tolist()), 'songs')

    # if bpm, then ask for range and get subset of dataframe
    elif choice == 'bpm':
        dataframe = ui.select_bpm()
        # print(dataframe)
        print('The min bpm is:', dataframe['bpm'].min(), '. The max bpm is:', dataframe['bpm'].max(),
              'with a total of', len(dataframe[section].tolist()), 'songs')

    # if both, then ask for artists and bpm_range
    elif choice == 'both':
        dataframe = ui.select_both()
        # print(dataframe)
        print('The min bpm is:', dataframe['bpm'].min(), '. The max bpm is:', dataframe['bpm'].max())
        print('There are', len(set(dataframe['artist'].tolist())), 'artists. These artists are:',
              set(dataframe['artist'].tolist()), 'with a total of', len(dataframe[section].tolist()), 'songs')

    # clean texts
    entries = dataframe[section].tolist()
    text = ''
    for entry in entries:
        text += entry.lower()
    return text
