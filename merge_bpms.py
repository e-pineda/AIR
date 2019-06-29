import pandas as pd


def merge():
    # READ BPMS
    bpm_df = pd.read_csv('bpms.csv')

    # READ SONG INFO
    song_df = pd.read_csv('rapper_scrape.csv')

    #ADD BPMS TO SONG_INFO DF
    song_df['bpm'] = bpm_df['BPM']

    # SORT DATAFRAME BY ARTIST NAME, THEN BY SONG NAME
    temp_df = song_df.sort_values(['artist', 'title'], ascending=[True, True])

    # SAVE VALUE
    temp_df.to_csv('final_info.csv', index=False)


def test():
    info_df = pd.read_csv('final_info.csv')
    print(info_df[['artist', 'title', 'bpm']])


# merge()
test()