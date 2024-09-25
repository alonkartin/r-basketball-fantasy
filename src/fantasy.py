


import                      pandas  as  pd
import                      warnings
warnings.filterwarnings("ignore")


# Definitions
myTeamName                  =   "Team 7"

numTeams                    =   8
numPlayersPerTeam           =   13

# Teams
ROTO8_DRAFT_ORDER           =   [   "Team 1", \
                                    "Team 2", \
                                    "Team 3", \
                                    "Team 4", \
                                    "Team 5", \
                                    "Team 6", \
                                    "Team 7", \
                                    "Team 8"]
                                    
                                    
SUMMARY_STATS                           =   ["PTS", "REB", "AST", "ST", "BLK", "TO", "3PTM"]
AVERAGE_STATS                           =   ["FG%", "FT%"]

stats_categories                        =   SUMMARY_STATS   +   AVERAGE_STATS
relevantColumns                         =   ["Player"]      +   stats_categories
draft_columns                           =   ["Team"]        +   relevantColumns

dataDir                                 =   "../data/"   
playerProjStatsFilepath                 =   dataDir + "proj_24_25_150_players.csv"


def loadPlayerProjStats(playerProjStatsFilepath):       
    print("loadPlayerProjStats")
    print("Loading player stats from: ", playerProjStatsFilepath)

    dfPlayerProjStats                   =   pd.read_csv(playerProjStatsFilepath)
    dfPlayerProjStats                   =   dfPlayerProjStats[relevantColumns]
    dfPlayerProjStats                   =   dfPlayerProjStats.astype({"PTS": float, "REB": float, "AST": float, "ST": float, "BLK": float, \
                                                                      "TO": float, "FG%": float, "FT%": float, "3PTM": float})
    return  dfPlayerProjStats
    
    
def updateDraft(dfDraft, teamName, dfPlayerProjStats, playerIndex):
    player                          =   dfPlayerProjStats.iloc[playerIndex]
    
    # create new dataframe with draft_columns. add a single row with the player's stats and the team name
    dfPlayer                        =   pd.DataFrame(columns=draft_columns)
    dfPlayer.loc[0]                 =   [teamName] + player.tolist()

    dfDraft                         =   pd.concat([dfDraft, dfPlayer], ignore_index=True)
    return  dfDraft
        
 
def getTeamDraft(dfDraft, teamName):

    dfTeamDraft                =   dfDraft[dfDraft["Team"] == teamName]

    #print("Team Draft for ", teamName)
    #print(dfTeamDraft)

    return dfTeamDraft
    
def getTeamDraftStats(dfDraft, teamName):
    dfTeamDraft = getTeamDraft(dfDraft, teamName)

    # create a new dataframe with the relevant columns and sum the stats
    dfTeamDraftStats                    =   pd.DataFrame(columns= ["Team"] + relevantColumns)

    statsRow                            =   {   'Team':     teamName, \
                                                'Player':   dfTeamDraft['Player'].sum(),
                                                'PTS':      dfTeamDraft['PTS'].sum(), \
                                                'REB':      dfTeamDraft['REB'].sum(), \
                                                'AST':      dfTeamDraft['AST'].sum(), \
                                                'ST':       dfTeamDraft['ST'].sum(), \
                                                'BLK':      dfTeamDraft['BLK'].sum(), \
                                                'TO':       dfTeamDraft['TO'].sum(), \
                                                '3PTM':     dfTeamDraft['3PTM'].sum(), \
                                                'FG%':      dfTeamDraft['FG%'].mean(), \
                                                'FT%':      dfTeamDraft['FT%'].mean()}
                                                
    dfTeamDraftStats.loc[0]             =   statsRow
    
    #print("Team Draft Stats for: ", teamName)
    #print(dfTeamDraftStats)

    return dfTeamDraftStats
    
 
def getAllTeamsDraftStats(dfDraft):
    dfTeamStats                         =   pd.DataFrame(columns= ["Team"] + relevantColumns)
    
    for teamName                        in  ROTO8_DRAFT_ORDER:
        dfTeamStats                     =   pd.concat([dfTeamStats, getTeamDraftStats(dfDraft, teamName)], ignore_index=True)

    return dfTeamStats
    
    
def noramlizeTeamsDraftStats(dfAllTeamsDraftStats, teamPlayerCountDct, dfDraft):

    # find the maximum number of players selected by each team
    maxPlayerCount                      =   max(teamPlayerCountDct.values())    

    # create a new dataframe with the relevant columns and sum the stats
    dfNormalizedTeamStats               =   pd.DataFrame(columns= ["Team"] + relevantColumns)


    for i, teamName                     in  enumerate(ROTO8_DRAFT_ORDER):

        # check if the team has selected any players
        if teamPlayerCountDct[teamName] ==  0:
            continue

        # check if the team has selected the maximum number of players
        if teamPlayerCountDct[teamName] ==  maxPlayerCount:
            dfNormalizedTeamStats.loc[i] =  dfAllTeamsDraftStats.loc[i]
            continue

        # Check if the team has selected less than the maximum number of players

        currTeamPlayerCount             =   teamPlayerCountDct[teamName]

        factor                          =   maxPlayerCount/currTeamPlayerCount

        dfTeamDraftStats                =   getTeamDraftStats(dfDraft, teamName)

        #print("Team Draft Stats for: ", teamName)
        #print(dfTeamDraftStats)

        statsRow                        =  {    'Team':     teamName, \
                                                'Player':   dfTeamDraftStats['Player'].values[0], \
                                                'PTS':      float(int(dfTeamDraftStats['PTS'].values[0]*factor)), \
                                                'REB':      float(int(dfTeamDraftStats['REB'].values[0]*factor)), \
                                                'AST':      float(int(dfTeamDraftStats['AST'].values[0]*factor)), \
                                                'ST':       float(int(dfTeamDraftStats['ST'].values[0]*factor)), \
                                                'BLK':      float(int(dfTeamDraftStats['BLK'].values[0]*factor)), \
                                                'TO':       float(int(dfTeamDraftStats['TO'].values[0]*factor)), \
                                                '3PTM':     float(int(dfTeamDraftStats['3PTM'].values[0]*factor)), \
                                                'FG%':      dfTeamDraftStats['FG%'].values[0], \
                                                'FT%':      dfTeamDraftStats['FT%'].values[0]}
        
        dfNormalizedTeamStats.loc[i]             =   statsRow

    return dfNormalizedTeamStats
    

def getTeamRankings(dfTeamStats, myTeamName):
    # create ranking dataframe, sort by each category separately (PTS	REB	AST	ST	BLK	TO	FG%	FT%	3PTM) and assign ranks. 
    
    dfRankings                                  =   pd.DataFrame(columns=["Team"])
    # add the team names to the rankings dataframe as new rows
    dfRankings["Team"]                          =   dfTeamStats["Team"]


    for category                                in  relevantColumns:
        # print("Category: ", category)

        # keep only the category column and the Team column and sort by that category column
        dfCategory                              =   dfTeamStats[["Team", category]].sort_values(by=category, ascending=True)

        # assign ranks
        dfCategory["Rank_" + category]          =   range(1, numTeams+1)

        # merge the ranks with the rankings dataframe
        dfRankings                              =   pd.merge(dfRankings, dfCategory, on="Team")

    # calculate the total score for each team
    dfRankings["Total Score"]                   =   dfRankings.filter(like="Rank").sum(axis=1)

    # sort by total score
    dfRankings                                  =   dfRankings.sort_values(by="Total Score", ascending=False)

    # find the row index of my team
    myTeamData                                  =   dfRankings[dfRankings["Team"] == myTeamName]

    # move my team to the top
    dfRankings                                  =   pd.concat([myTeamData, dfRankings[dfRankings["Team"] != myTeamName]])   

    return dfRankings
    
def evaluateSelection(dfDraft, dfPlayerProjStats, myTeamName, playerIndex):
    # update the draft dataframe with the new player
    dfDraft                                     =   updateDraft(dfDraft, myTeamName, dfPlayerProjStats, playerIndex)
    # calculate the total score for each team
    dfTeamStats                                 =   getAllTeamsDraftStats(dfDraft)
    dfRankings                                  =   getTeamRankings(dfTeamStats, myTeamName)   
    return dfRankings
    

def evaluateSelections(dfDraft, dfPlayerProjStats, myTeamName, playerIndexLst):   
    dctSelectionsRankings                       =   {}  
    
    for playerIndex                             in  playerIndexLst:
        dfRankings                              =   evaluateSelection(dfDraft, dfPlayerProjStats, myTeamName, playerIndex)
        #print("Player Index: ", playerIndex)
        #print(dfRankings)
        #print("\n\n")

        dctSelectionsRankings[playerIndex]      =   dfRankings

    return dctSelectionsRankings
    
def getMyTeamRankings(playerIndexLst, dfDraft, dfPlayerProjStats, myTeamName, dfRankings):
    dctSelectionsRankings                           =   evaluateSelections(dfDraft, dfPlayerProjStats, myTeamName, playerIndexLst)

    dfMyTeamRankings                                =   pd.DataFrame(columns=dctSelectionsRankings[playerIndexLst[0]].columns)
                                        
    # iterate over the dictionary and print the rankings for each player selection
    for playerIndex in playerIndexLst:
        #print("Player Index: ", playerIndex)
        currSelectionRank                 =   dctSelectionsRankings[playerIndex]

        myTeamData = currSelectionRank[currSelectionRank["Team"] == myTeamName]

        myTeamData["Player"] = dfPlayerProjStats.iloc[playerIndex]["Player"]
        
        dfMyTeamRankings = pd.concat([dfMyTeamRankings, myTeamData])

    # sort by total score
    dfMyTeamRankings = dfMyTeamRankings.sort_values(by="Total Score", ascending=False)

    # get my current team ranking from dfRankings
    myTeamRank = dfRankings[dfRankings["Team"] == myTeamName]


    dfMyTeamRankings = pd.concat([myTeamRank ,dfMyTeamRankings])

    dfMyTeamRankings

    return dfMyTeamRankings


dfPlayerProjStats                       =   loadPlayerProjStats(playerProjStatsFilepath)

print(dfPlayerProjStats.head())


dfDraft                                 =   pd.DataFrame(columns=draft_columns)   

# create a list of number of players selected per team. initialize to 0 for all teams
teamPlayerCountDct                      =   {}

for team                                in  ROTO8_DRAFT_ORDER:
    teamPlayerCountDct[team]            =   0

stopIndex                               =   51 # numPlayersPerTeam*numTeams

index = 0
for choice                              in  range(0, numPlayersPerTeam):    
    for i, team                         in  enumerate(ROTO8_DRAFT_ORDER):
        if index                        >=  stopIndex:
            break

        dfDraft                         =   updateDraft(dfDraft, team, dfPlayerProjStats, index)
        teamPlayerCountDct[team]        +=  1
        index                           +=  1

print(dfDraft)  # , teamPlayerCountDct


dfAllTeamsDraftStats                                 =   getAllTeamsDraftStats(dfDraft)
print(dfAllTeamsDraftStats)

#test
if False:
    teamPlayerCountDct['Team 5'] = 12
    teamPlayerCountDct['Team 6'] = 12
    teamPlayerCountDct['Team 7'] = 12
    teamPlayerCountDct['Team 8'] = 12

print(teamPlayerCountDct)

dfNormAllTeamsDraftStats                            =   noramlizeTeamsDraftStats(dfAllTeamsDraftStats, teamPlayerCountDct, dfDraft)
print(dfNormAllTeamsDraftStats)

print(dfAllTeamsDraftStats)

dfRankings                                          =   getTeamRankings(dfAllTeamsDraftStats,myTeamName)
print(dfRankings)

dfNormRankings                                      =   getTeamRankings(dfNormAllTeamsDraftStats,myTeamName)
print(dfNormRankings)

playerIndexLst                                      =   [10, 20, 30]
dfMyTeamRankings                                    =   getMyTeamRankings(playerIndexLst, dfDraft, dfPlayerProjStats, myTeamName, dfRankings)
print(dfMyTeamRankings)