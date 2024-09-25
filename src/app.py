import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import streamlit as st

# Definitions
myTeamName = "Team 7"

numTeams = 8
numPlayersPerTeam = 13

# Teams
ROTO8_DRAFT_ORDER = [
    "Team 1",
    "Team 2",
    "Team 3",
    "Team 4",
    "Team 5",
    "Team 6",
    "Team 7",
    "Team 8",
]

SUMMARY_STATS = ["PTS", "REB", "AST", "ST", "BLK", "TO", "3PTM"]
AVERAGE_STATS = ["FG%", "FT%"]

stats_categories = SUMMARY_STATS + AVERAGE_STATS
relevantColumns = ["Player"] + stats_categories
draft_columns = ["Team"] + relevantColumns

# Load data
@st.cache
def loadPlayerProjStats(uploaded_file):       
    dfPlayerProjStats = pd.read_csv(uploaded_file)
    dfPlayerProjStats = dfPlayerProjStats[relevantColumns]
    dfPlayerProjStats = dfPlayerProjStats.astype({
        "PTS": float,
        "REB": float,
        "AST": float,
        "ST": float,
        "BLK": float,
        "TO": float,
        "FG%": float,
        "FT%": float,
        "3PTM": float,
    })
    return dfPlayerProjStats

def updateDraft(dfDraft, teamName, dfPlayerProjStats, playerIndex):
    player = dfPlayerProjStats.iloc[playerIndex]

    # Create new dataframe with draft_columns. Add a single row with the player's stats and the team name
    dfPlayer = pd.DataFrame(columns=draft_columns)
    dfPlayer.loc[0] = [teamName] + player.tolist()

    dfDraft = pd.concat([dfDraft, dfPlayer], ignore_index=True)
    return dfDraft

def getTeamDraft(dfDraft, teamName):
    dfTeamDraft = dfDraft[dfDraft["Team"] == teamName]
    return dfTeamDraft

def getTeamDraftStats(dfDraft, teamName):
    dfTeamDraft = getTeamDraft(dfDraft, teamName)

    # Sum the stats
    statsRow = {
        'Team': teamName,
        'Player': ', '.join(dfTeamDraft['Player'].tolist()),
        'PTS': dfTeamDraft['PTS'].sum(),
        'REB': dfTeamDraft['REB'].sum(),
        'AST': dfTeamDraft['AST'].sum(),
        'ST': dfTeamDraft['ST'].sum(),
        'BLK': dfTeamDraft['BLK'].sum(),
        'TO': dfTeamDraft['TO'].sum(),
        '3PTM': dfTeamDraft['3PTM'].sum(),
        'FG%': dfTeamDraft['FG%'].mean(),
        'FT%': dfTeamDraft['FT%'].mean(),
    }

    dfTeamDraftStats = pd.DataFrame([statsRow], columns=["Team"] + relevantColumns)
    return dfTeamDraftStats

def getAllTeamsDraftStats(dfDraft):
    dfTeamStats = pd.DataFrame(columns=["Team"] + relevantColumns)
    for teamName in ROTO8_DRAFT_ORDER:
        dfTeamStats = pd.concat([dfTeamStats, getTeamDraftStats(dfDraft, teamName)], ignore_index=True)
    return dfTeamStats

def getTeamRankings(dfTeamStats, myTeamName):
    dfRankings = pd.DataFrame(columns=["Team"])
    dfRankings["Team"] = dfTeamStats["Team"]

    for category in stats_categories:
        ascending = False  # Higher stats are better
        if category == "TO":  # For turnovers, lower is better
            ascending = True
        dfRankings["Rank_" + category] = dfTeamStats[category].rank(ascending=ascending, method='min')

    # Calculate the total score for each team
    dfRankings["Total Score"] = dfRankings.filter(like="Rank").sum(axis=1)

    # Sort by total score
    dfRankings = dfRankings.sort_values(by="Total Score", ascending=True)

    # Move my team to the top
    myTeamData = dfRankings[dfRankings["Team"] == myTeamName]
    dfRankings = pd.concat([myTeamData, dfRankings[dfRankings["Team"] != myTeamName]])

    return dfRankings

def evaluateSelection(dfDraft, dfPlayerProjStats, myTeamName, playerIndex):
    # Update the draft dataframe with the new player
    dfDraft = updateDraft(dfDraft.copy(), myTeamName, dfPlayerProjStats, playerIndex)
    # Calculate the total score for each team
    dfTeamStats = getAllTeamsDraftStats(dfDraft)
    dfRankings = getTeamRankings(dfTeamStats, myTeamName)
    return dfRankings

def evaluateSelections(dfDraft, dfPlayerProjStats, myTeamName, playerIndexLst):
    dctSelectionsRankings = {}
    for playerIndex in playerIndexLst:
        dfRankings = evaluateSelection(dfDraft.copy(), dfPlayerProjStats, myTeamName, playerIndex)
        dctSelectionsRankings[playerIndex] = dfRankings
    return dctSelectionsRankings

def getMyTeamRankings(playerIndexLst, dfDraft, dfPlayerProjStats, myTeamName, dfRankings):
    dctSelectionsRankings = evaluateSelections(dfDraft.copy(), dfPlayerProjStats, myTeamName, playerIndexLst)
    dfMyTeamRankings = pd.DataFrame(columns=dctSelectionsRankings[playerIndexLst[0]].columns)

    # Iterate over the dictionary and get the rankings for each player selection
    for playerIndex in playerIndexLst:
        currSelectionRank = dctSelectionsRankings[playerIndex]
        myTeamData = currSelectionRank[currSelectionRank["Team"] == myTeamName]
        myTeamData["Player"] = dfPlayerProjStats.iloc[playerIndex]["Player"]
        dfMyTeamRankings = pd.concat([dfMyTeamRankings, myTeamData])

    # Sort by total score
    dfMyTeamRankings = dfMyTeamRankings.sort_values(by="Total Score", ascending=True)

    # Get my current team ranking from dfRankings
    myTeamRank = dfRankings[dfRankings["Team"] == myTeamName]

    dfMyTeamRankings = pd.concat([myTeamRank, dfMyTeamRankings])

    return dfMyTeamRankings

def simulate_picks_up_to_my_turn(dfDraft, dfPlayerProjStats, teamPlayerCountDct):
    while True:
        pick_number = st.session_state.pick_number
        # Determine which team's turn it is
        team_index = pick_number % len(ROTO8_DRAFT_ORDER)
        team_name = ROTO8_DRAFT_ORDER[team_index]

        if team_name == myTeamName:
            # It's our turn, break the loop
            break
        else:
            # Simulate pick for other team
            available_players = dfPlayerProjStats[~dfPlayerProjStats['Player'].isin(dfDraft['Player'])]
            if len(available_players) == 0:
                st.write("No more available players.")
                return
            # Pick the top available player
            player_index = available_players.index[0]
            dfDraft = updateDraft(dfDraft, team_name, dfPlayerProjStats, player_index)
            teamPlayerCountDct[team_name] += 1

            st.session_state.dfDraft = dfDraft
            st.session_state.teamPlayerCountDct = teamPlayerCountDct
            st.session_state.pick_number += 1

# Streamlit App
st.title("Fantasy Basketball Draft Simulator")

# Upload player projection CSV file
uploaded_file = st.file_uploader("Choose a player projection CSV file", type="csv")

if uploaded_file is not None:
    dfPlayerProjStats = loadPlayerProjStats(uploaded_file)

    # Initialize session state variables
    if 'dfDraft' not in st.session_state:
        st.session_state.dfDraft = pd.DataFrame(columns=draft_columns)
    if 'teamPlayerCountDct' not in st.session_state:
        st.session_state.teamPlayerCountDct = {team: 0 for team in ROTO8_DRAFT_ORDER}
    if 'pick_number' not in st.session_state:
        st.session_state.pick_number = 0

    # Simulate picks up to user's turn
    simulate_picks_up_to_my_turn(
        st.session_state.dfDraft,
        dfPlayerProjStats,
        st.session_state.teamPlayerCountDct,
    )

    st.subheader("Your Turn to Pick")

    # Get available players
    available_players = dfPlayerProjStats[
        ~dfPlayerProjStats['Player'].isin(st.session_state.dfDraft['Player'])
    ]

    # Show top 20 available players
    top_available_players = available_players.head(20)
    st.write("Top Available Players:")
    st.dataframe(top_available_players)

    # Allow user to select a player
    player_names = top_available_players['Player'].tolist()
    selected_player = st.selectbox('Select a player to draft:', player_names)

    # Evaluate potential selections
    playerIndexLst = top_available_players.index.tolist()
    dfAllTeamsDraftStats = getAllTeamsDraftStats(st.session_state.dfDraft)
    dfRankings = getTeamRankings(dfAllTeamsDraftStats, myTeamName)
    dfMyTeamRankings = getMyTeamRankings(
        playerIndexLst,
        st.session_state.dfDraft,
        dfPlayerProjStats,
        myTeamName,
        dfRankings,
    )

    st.write("Potential Team Rankings for Possible Selections:")
    st.dataframe(dfMyTeamRankings)

    if st.button('Draft Player'):
        # Find the index of the selected player in dfPlayerProjStats
        player_index = dfPlayerProjStats[dfPlayerProjStats['Player'] == selected_player].index[0]

        # Update the draft
        dfDraft = updateDraft(
            st.session_state.dfDraft,
            myTeamName,
            dfPlayerProjStats,
            player_index,
        )
        st.session_state.dfDraft = dfDraft

        # Update team player count
        teamPlayerCountDct = st.session_state.teamPlayerCountDct
        teamPlayerCountDct[myTeamName] += 1
        st.session_state.teamPlayerCountDct = teamPlayerCountDct

        # Update pick number
        st.session_state.pick_number += 1

        # Success message
        st.success(f"You have drafted {selected_player}.")

        # Simulate picks up to next user turn
        simulate_picks_up_to_my_turn(
            st.session_state.dfDraft,
            dfPlayerProjStats,
            st.session_state.teamPlayerCountDct,
        )

    # Display user's team
    dfMyTeamDraft = getTeamDraft(st.session_state.dfDraft, myTeamName)
    st.subheader("Your Team:")
    st.dataframe(dfMyTeamDraft)

    # Display team rankings
    dfAllTeamsDraftStats = getAllTeamsDraftStats(st.session_state.dfDraft)
    dfRankings = getTeamRankings(dfAllTeamsDraftStats, myTeamName)
    st.subheader("Current Team Rankings:")
    st.dataframe(dfRankings)

else:
    st.info("Please upload a player projection CSV file to start the simulation.")
