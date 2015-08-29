import csv
import pandas as pd
import re
import operator

# We need this for our roster
# 1 qb, 2 wr, 2rb, 1 te, 1 fx, 1 kr, 1 df, 7bench

# TODO: set POS_MAX['rb'] = 5 and run through multiple rb's until you run out
# TODO: when you run out of that rank, you should still be able to see low scores based on min values

POS_MAX = {'qb': 1, 'wr': 2, 'rb': 2, 'te': 1, 'fx': 1, 'kr': 1, 'df': 1}

# Also, assume 10 people in the league
NUM_TEAMS = 10


# <<<--- BEGIN: Do data transformation --->>>
sources = ['cbs', 'espn', 'nfl', 'fp']
positions = ['qb', 'kr', 'df', 'rb', 'wr', 'te']

espn_data = []
cbs_data = []
nfl_data = []
fp_data = []

for source in sources:
    for position in positions:
        with open("data/{0}_{1}.csv".format(source, position)) as f:
            csv_r = csv.reader(f, delimiter=',')
            for i, line in enumerate(csv_r):
                if i == 0:
                    continue
                if source == 'espn':
                    record = {}
                    record['source'] = source
                    record['position'] = position
                    record['player'] = line[1].split(',')[0]
                    record['pts'] = line[-1]
                    espn_data.append(record)
                elif source == 'cbs':
                    record = {}
                    record['source'] = source
                    record['position'] = position
                    record['player'] = line[0].split(',')[0]
                    record['pts'] = line[-1]
                    cbs_data.append(record)
                elif source == 'nfl':
                    record = {}
                    record['source'] = source
                    record['position'] = position

                    # Scrub nfl player field
                    if position == 'kr':
                        player = re.sub('[A-Z] - [A-Z][A-Z].*$', '', line[0].split(',')[0]).rstrip()
                    else:
                        player = re.sub('[A-Z][A-Z] - [A-Z][A-Z].*$', '', line[0].split(',')[0]).rstrip()

                        # Ugly way to get rid of some ugly data
                        player = player.replace(' TE', '')
                        player = player.replace(' DEF', '')
                        player = player.replace(' View Videos', '')
                        player = player.replace('*', '')

                    record['player'] = player

                    record['pts'] = line[-1]
                    nfl_data.append(record)
                elif source == 'fp':
                    record = {}
                    record['position'] = position
                    record['player'] = line[0].split(',')[0]
                    record['pts'] = line[-1]
                    #print record
                    fp_data.append(record)

#df_cbs = pd.DataFrame.from_dict(cbs_data)
#df_espn = pd.DataFrame.from_dict(espn_data)
#df_nfl = pd.DataFrame.from_dict(nfl_data)

# Which data sets should we use?
# cbs_data, espn_data, nfl_data, fp_data
raw_data = [espn_data, nfl_data, fp_data]
scrubbed_data = {}
for i, lst in enumerate(raw_data):
    for j, rec in enumerate(lst):
        if rec['pts'] in ('0', '1', '--'):
            continue

        if scrubbed_data.get((rec['position'], rec['player'])):
            scrubbed_data[(rec['position'], rec['player'])].append(float(rec['pts']))
        else:
            scrubbed_data[(rec['position'], rec['player'])] = [float(rec['pts'])]

final_lst = []

for i, k in enumerate(scrubbed_data.iteritems()):
    if len(k[1]) > 1:
        avg = reduce(lambda x, y: x + y, k[1]) / len(k[1])
        avg_pts = [val for val in k[0]]
        avg_pts.append(avg)
        final_lst.append(avg_pts)

# Configure main data frame of pool of players
df = pd.DataFrame(final_lst)
df.rename(columns={0: 'pos', 1: 'player', 2: 'pts'}, inplace=True)
df['player_name'] = df['player']
df = df.set_index('player')

# Configure empty data for players that I select
my_df = None

# <<<--- END: Do data transformation --->>>







# <<<--- BEGIN: Start program loop based on transformed data --->>>

while True:
    df['rank'] = df.groupby(['pos'])['pts'].rank(method='dense', ascending=False)

    # Print our team
    # TODO: Pretty print our team
    if my_df is not None:
        if not my_df.empty:
            print '<<<--- Our Awesome Team Lineup --->>>'
            print my_df
            print

    # Print next best CPV
    print '<<<--- Next Best Player Based on CPV --->>>'
    print 'pos | cpv | fpts | player'
    print '-----------------------------'
    lst = []
    for k, v in POS_MAX.iteritems():
        high_val = df.query("pos=='{pos}' & rank=={rank}".format(pos=k, rank=v))
        low_val = df.query("pos=='{pos}' & rank=={rank}".format(pos=k, rank=v*NUM_TEAMS))

        high, low = high_val['pts'].tolist(), low_val['pts'].tolist()
        high_player, low_player = high_val.index.values, low_val.index.values

        if not low or not high:
            continue

        lst.append([k.upper(), "{0:.1f}".format(high[0] - low[0]), "{0:.1f}".format(high[0]), high_player[0]])

    sortedL = sorted(lst, key=operator.itemgetter(1), reverse=True)
    for line in sortedL:
        print line[0], '|', line[1], '|', line[2], '|', line[3]
    print

    # Search a player
    input_name = raw_input('Lookup a player: ')
    player_df = df[df['player_name'].str.contains("{0}".format(input_name))==True]
    find_cnt = len(player_df)

    # Handle errors in player search
    if find_cnt == 0:
        print "<<<---WARNING: No players found! Resetting!--->>>\n"
        continue

    if len(player_df) > 1:
        print "<<<---WARNING: Found {0} players with that name. Be more specific!--->>>\n".format(len(player_df))
        print player_df
        print
        print "<<<---WARNING: Resetting!--->>>\n"
        continue

    print
    print "Found this player... \n", player_df
    print

    # Enter prompt to decide if we drafted this person or another team
    del_player = raw_input('Did we draft this person (y/n): ')
    print

    player_to_delete = player_df['player_name'][0]


    if del_player == 'y':
        # If you drafted this person, put him in my_df
        if my_df is None:
            my_df = df[df.player_name == player_to_delete]
        else:
            my_df = pd.concat([my_df, df[df.player_name == player_to_delete]])

        # Don't forget to remove him from the main df
        df = df[df.player_name != player_to_delete]
    else:
        df = df[df.player_name != player_to_delete]
        continue

# <<<--- END: Start program loop based on data transformed --->>>







"""
grouped_espn = df_espn.groupby(by='position')
print grouped_espn.count()

grouped_cbs = df_cbs.groupby(by='position')
print grouped_cbs.count()

grouped_nfl = df_nfl.groupby(by='position')
print grouped_nfl.count()

# set index to player
#cbs = df_cbs.set_index('player', 'position')
#espn = df_espn.set_index('player', 'position')

# Join both data frames
df = pd.merge(df_espn, df_cbs, how='inner', on=['player', 'position'])

# Convert to numeric
df[['pts_x', 'pts_y']] = df[['pts_x', 'pts_y']].astype(float)

# Apply function to get avg or value that exists for each player
df['avgs'] = (df.pts_x + df.pts_y)/2
#print df


# Drop unnecessary columns
df.drop(['source_y', 'source_x', 'pts_x', 'pts_y'], axis=1, inplace=True)

# Set index to player-name
df = df.set_index('player', 'position')
print df

# Do group by per position and aggregate
# Check out the averages
grouped = df['avgs'].groupby(df['position'])
print grouped.mean()
"""