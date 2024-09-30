import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import streamlit as st
import random

# Definitions
numTeams = 8
numPlayersPerTeam = 13

# Summary and Average Stats
SUMMARY_STATS = ["PTS", "REB", "AST", "ST", "BLK", "3PTM"]
LOWER_BETTER_STATS = ["TO"]  # Lower stats are better for turnovers
AVERAGE_STATS = ["FG%", "FT%"]

stats_categories = SUMMARY_STATS + LOWER_BETTER_STATS + AVERAGE_STATS
relevantColumns = ["Player"] + stats_categories
draft_columns = ["Team"] + relevantColumns

# Predefined Target Goals
TARGET_GOALS = {
    "PTS": 17499,
    "REB": 6423,
    "AST": 4048,
    "ST": 969,
    "BLK": 640,
    "3PTM": 1500,
    "TO": 2097,
    "FG%": 0.484,
    "FT%": 0.796
}

# Load data
@st.cache_data
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
    dfTeamDraft = dfDraft[dfDraft["Team"] == teamName].copy()
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
        'FG%': dfTeamDraft['FG%'].mean() if not dfTeamDraft.empty else 0,
        'FT%': dfTeamDraft['FT%'].mean() if not dfTeamDraft.empty else 0,
    }

    dfTeamDraftStats = pd.DataFrame([statsRow], columns=["Team"] + relevantColumns)
    return dfTeamDraftStats

def getAllTeamsDraftStats(dfDraft, team_order):
    dfTeamStats = pd.DataFrame(columns=["Team"] + relevantColumns)
    for teamName in team_order:
        dfTeamStats = pd.concat([dfTeamStats, getTeamDraftStats(dfDraft, teamName)], ignore_index=True)
    return dfTeamStats

def getTeamRankings(dfTeamStats, myTeamName):
    dfRankings = pd.DataFrame(columns=["Team"])
    dfRankings["Team"] = dfTeamStats["Team"]
    numTeams = len(dfTeamStats)

    for category in stats_categories:
        if category in LOWER_BETTER_STATS:
            ascending = True  # Lower stats are better
        else:
            ascending = False  # Higher stats are better

        # Compute ranks
        dfRankings["Rank_" + category] = dfTeamStats[category].rank(ascending=ascending, method='min')
        # Adjust ranks so that higher rank numbers are better
        dfRankings["Rank_" + category] = numTeams + 1 - dfRankings["Rank_" + category]

    # Calculate the total score for each team
    dfRankings["Total Score"] = dfRankings.filter(like="Rank_").sum(axis=1)

    # Sort by total score
    dfRankings = dfRankings.sort_values(by="Total Score", ascending=False)

    # Move my team to the top
    myTeamData = dfRankings[dfRankings["Team"] == myTeamName]
    dfRankings = pd.concat([myTeamData, dfRankings[dfRankings["Team"] != myTeamName]])

    return dfRankings

def evaluateSelection(dfDraft, dfPlayerProjStats, myTeamName, playerIndex, team_order):
    # Update the draft dataframe with the new player
    dfDraft = updateDraft(dfDraft.copy(), myTeamName, dfPlayerProjStats, playerIndex)
    # Calculate the total score for each team
    dfTeamStats = getAllTeamsDraftStats(dfDraft, team_order)
    dfRankings = getTeamRankings(dfTeamStats, myTeamName)
    return dfRankings

def evaluateSelections(dfDraft, dfPlayerProjStats, myTeamName, playerIndexLst, team_order):
    dctSelectionsRankings = {}
    for playerIndex in playerIndexLst:
        dfRankings = evaluateSelection(dfDraft.copy(), dfPlayerProjStats, myTeamName, playerIndex, team_order)
        dctSelectionsRankings[playerIndex] = dfRankings
    return dctSelectionsRankings

def getMyTeamRankings(playerIndexLst, dfDraft, dfPlayerProjStats, myTeamName, dfRankings, team_order):
    dctSelectionsRankings = evaluateSelections(dfDraft.copy(), dfPlayerProjStats, myTeamName, playerIndexLst, team_order)
    dfMyTeamRankings = pd.DataFrame(columns=dctSelectionsRankings[playerIndexLst[0]].columns)

    # Iterate over the dictionary and get the rankings for each player selection
    for playerIndex in playerIndexLst:
        currSelectionRank = dctSelectionsRankings[playerIndex]
        myTeamData = currSelectionRank[currSelectionRank["Team"] == myTeamName]
        myTeamData["Player"] = dfPlayerProjStats.iloc[playerIndex]["Player"]
        dfMyTeamRankings = pd.concat([dfMyTeamRankings, myTeamData])

    # Sort by total score
    dfMyTeamRankings = dfMyTeamRankings.sort_values(by="Total Score", ascending=False)

    # Get my current team ranking from dfRankings
    myTeamRank = dfRankings[dfRankings["Team"] == myTeamName]

    dfMyTeamRankings = pd.concat([myTeamRank, dfMyTeamRankings])

    return dfMyTeamRankings

def generate_snake_draft_order(num_teams, num_rounds):
    order = []
    teams = list(range(num_teams))
    for round_num in range(num_rounds):
        if round_num % 2 == 0:
            # Normal order
            order.extend(teams)
        else:
            # Reversed order
            order.extend(reversed(teams))
    return order

def simulate_or_manual_picks(dfDraft, dfPlayerProjStats, teamPlayerCountDct, mode, myTeamIndex, snake_draft_order, team_order):
    while True:
        pick_number = st.session_state.pick_number
        if pick_number >= len(snake_draft_order):
            st.write("Draft is complete.")
            return
        team_index = snake_draft_order[pick_number]
        team_name = team_order[team_index]

        if team_index == myTeamIndex:
            # It's our turn, break the loop
            break
        else:
            # Simulate or manually pick for other team
            available_players = dfPlayerProjStats[
                ~dfPlayerProjStats['Player'].isin(st.session_state.dfDraft['Player'])
            ]
            if len(available_players) == 0:
                st.write("No more available players.")
                return
            if mode == "Manual Input":
                st.subheader(f"{team_name}'s Turn to Pick")
                # Show top available players
                top_available_players = available_players.head(20)
                st.write("Top Available Players for Other Teams:")
                st.dataframe(top_available_players)
                # Allow user to select a player for the other team
                player_names = top_available_players['Player'].tolist()
                selected_player = st.selectbox(f"Select a player for {team_name}:", player_names, key=f"select_{pick_number}")
                # Wait for user to select and confirm
                if not st.button(f"Confirm selection for {team_name}", key=f"button_{pick_number}"):
                    return  # Wait until user makes a selection
                # Find the index of the selected player
                player_index = dfPlayerProjStats[dfPlayerProjStats['Player'] == selected_player].index[0]
            else:
                # Automatic Simulation
                top_n = 5 if mode == "Automatic - Random from Top 5" else 1
                top_available_players = available_players.head(top_n)
                if mode == "Automatic - Random from Top 5":
                    # Randomly select from top 5 available players
                    selected_player_row = top_available_players.sample(1)
                else:
                    # Select the top available player
                    selected_player_row = top_available_players.head(1)
                selected_player = selected_player_row.iloc[0]['Player']
                player_index = selected_player_row.index[0]

            # Before making changes, save the current state for Undo functionality
            save_current_state()

            # Update the draft
            dfDraft = updateDraft(dfDraft, team_name, dfPlayerProjStats, player_index)
            teamPlayerCountDct[team_name] += 1

            st.session_state.dfDraft = dfDraft
            st.session_state.teamPlayerCountDct = teamPlayerCountDct
            st.session_state.pick_number += 1

# Function to save the current state before making changes
def save_current_state():
    # Create a snapshot of the current state
    state_snapshot = {
        'dfDraft': st.session_state.dfDraft.copy(),
        'teamPlayerCountDct': st.session_state.teamPlayerCountDct.copy(),
        'pick_number': st.session_state.pick_number,
    }
    # Append to draft history
    st.session_state.draft_history.append(state_snapshot)
    # Clear redo stack since we have a new action
    st.session_state.redo_stack.clear()

# Function to undo the last action
def undo_action():
    if st.session_state.draft_history:
        # Save current state to redo stack
        current_state = {
            'dfDraft': st.session_state.dfDraft.copy(),
            'teamPlayerCountDct': st.session_state.teamPlayerCountDct.copy(),
            'pick_number': st.session_state.pick_number,
        }
        st.session_state.redo_stack.append(current_state)
        # Restore the last state from history
        last_state = st.session_state.draft_history.pop()
        st.session_state.dfDraft = last_state['dfDraft']
        st.session_state.teamPlayerCountDct = last_state['teamPlayerCountDct']
        st.session_state.pick_number = last_state['pick_number']
        st.success("Undid the last action.")
    else:
        st.warning("Nothing to undo.")

# Function to redo the last undone action
def redo_action():
    if st.session_state.redo_stack:
        # Save current state to draft history
        current_state = {
            'dfDraft': st.session_state.dfDraft.copy(),
            'teamPlayerCountDct': st.session_state.teamPlayerCountDct.copy(),
            'pick_number': st.session_state.pick_number,
        }
        st.session_state.draft_history.append(current_state)
        # Restore the next state from redo stack
        next_state = st.session_state.redo_stack.pop()
        st.session_state.dfDraft = next_state['dfDraft']
        st.session_state.teamPlayerCountDct = next_state['teamPlayerCountDct']
        st.session_state.pick_number = next_state['pick_number']
        st.success("Redid the last undone action.")
    else:
        st.warning("Nothing to redo.")

# Streamlit App
st.title("Fantasy Basketball Draft Simulator")

# Initialize session state for Undo/Redo functionality
if 'draft_history' not in st.session_state:
    st.session_state.draft_history = []
if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []

# Upload player projection CSV file
uploaded_file = st.file_uploader("Choose a player projection CSV file", type="csv")

if uploaded_file is not None:
    dfPlayerProjStats = loadPlayerProjStats(uploaded_file)

    # Enter your team name
    myTeamName = st.text_input("Enter your team name:", value="My Team")

    # Select your team's draft position
    myTeamIndex = st.number_input(
        f"Select your team's draft position (1-{numTeams}):",
        min_value=1,
        max_value=numTeams,
        value=1,
        step=1
    ) - 1  # Zero-based index

    # Select mode
    mode = st.selectbox(
        "Select Draft Mode for Other Teams:",
        ["Automatic - Top Pick", "Automatic - Random from Top 5", "Manual Input"],
        index=0
    )

    # Start Draft button
    if st.button("Start Draft") or 'draft_started' in st.session_state:
        if 'draft_started' not in st.session_state:
            st.session_state.draft_started = True

            # Initialize team names
            team_order = [f"Team {i+1}" for i in range(numTeams)]
            # Replace the team at myTeamIndex with user's team name
            team_order[myTeamIndex] = myTeamName
            st.session_state.myTeamName = myTeamName
            st.session_state.myTeamIndex = myTeamIndex
            st.session_state.team_order = team_order

            # Initialize team player counts
            st.session_state.teamPlayerCountDct = {team: 0 for team in team_order}

            # Initialize the draft dataframe
            st.session_state.dfDraft = pd.DataFrame(columns=draft_columns)

            # Initialize pick number
            st.session_state.pick_number = 0

            # Generate snake draft order
            total_picks = numTeams * numPlayersPerTeam
            num_rounds = total_picks // numTeams
            snake_draft_order = generate_snake_draft_order(numTeams, num_rounds)
            st.session_state.snake_draft_order = snake_draft_order

        # Proceed with the draft
        myTeamName = st.session_state.myTeamName
        myTeamIndex = st.session_state.myTeamIndex
        team_order = st.session_state.team_order

        # Undo and Redo Buttons
        col1, col2 = st.columns(2)
        if col1.button("Undo"):
            undo_action()
        if col2.button("Redo"):
            redo_action()

        # Simulate or manually pick for other teams up to user's turn
        simulate_or_manual_picks(
            st.session_state.dfDraft,
            dfPlayerProjStats,
            st.session_state.teamPlayerCountDct,
            mode,
            myTeamIndex,
            st.session_state.snake_draft_order,
            team_order,
        )

        st.subheader("Your Turn to Pick")

        # Get available players
        available_players = dfPlayerProjStats[
            ~dfPlayerProjStats['Player'].isin(st.session_state.dfDraft['Player'])
        ]

        if not available_players.empty:
            # Show top 20 available players
            top_available_players = available_players.head(20)
            st.write("Top Available Players:")
            st.dataframe(top_available_players)

            # Allow user to select a player
            player_names = top_available_players['Player'].tolist()
            selected_player = st.selectbox('Select a player to draft:', player_names)

            # Evaluate potential selections
            playerIndexLst = top_available_players.index.tolist()
            dfAllTeamsDraftStats = getAllTeamsDraftStats(st.session_state.dfDraft, team_order)
            dfRankings = getTeamRankings(dfAllTeamsDraftStats, myTeamName)
            dfMyTeamRankings = getMyTeamRankings(
                playerIndexLst,
                st.session_state.dfDraft,
                dfPlayerProjStats,
                myTeamName,
                dfRankings,
                team_order,
            )

            st.write("Potential Team Rankings for Possible Selections:")
            st.dataframe(dfMyTeamRankings)

            if st.button('Draft Player'):
                # Before making changes, save the current state for Undo functionality
                save_current_state()

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

                # Clear redo stack after new action
                st.session_state.redo_stack.clear()

                # Success message
                st.success(f"You have drafted {selected_player}.")

                # Simulate or manually pick for other teams up to next user turn
                simulate_or_manual_picks(
                    st.session_state.dfDraft,
                    dfPlayerProjStats,
                    st.session_state.teamPlayerCountDct,
                    mode,
                    myTeamIndex,
                    st.session_state.snake_draft_order,
                    team_order,
                )
        else:
            st.write("No more available players to draft.")

        # Display user's team
        dfMyTeamDraft = getTeamDraft(st.session_state.dfDraft, myTeamName)
        st.subheader("Your Team:")

        # Calculate team totals and averages
        team_totals = dfMyTeamDraft[stats_categories].sum(numeric_only=True)
        team_averages = dfMyTeamDraft[AVERAGE_STATS].mean(numeric_only=True)
        # Combine totals and averages
        team_stats = team_totals.copy()
        team_stats.update(team_averages)

        # Create DataFrame for team stats
        dfTeamStats = pd.DataFrame([team_stats], columns=stats_categories)
        dfTeamStats['Player'] = 'Team Totals'
        dfTeamStats['Team'] = ''
        dfTeamStats = dfTeamStats[draft_columns[1:]]

        # Create DataFrame for target goals
        dfTargetGoals = pd.DataFrame([TARGET_GOALS], columns=stats_categories)
        dfTargetGoals['Player'] = 'Target Goals'
        dfTargetGoals['Team'] = ''
        dfTargetGoals = dfTargetGoals[draft_columns[1:]]

        # Append team stats and target goals to your team DataFrame
        dfMyTeamDisplay = pd.concat([dfMyTeamDraft[draft_columns[1:]], dfTeamStats, dfTargetGoals], ignore_index=True)

        st.dataframe(dfMyTeamDisplay)

        # Display team rankings
        dfAllTeamsDraftStats = getAllTeamsDraftStats(st.session_state.dfDraft, team_order)
        dfRankings = getTeamRankings(dfAllTeamsDraftStats, myTeamName)
        st.subheader("Current Team Rankings:")
        st.dataframe(dfRankings)

        # Optionally display the full draft
        if st.checkbox("Show Full Draft Results"):
            st.subheader("Full Draft Results:")
            st.dataframe(st.session_state.dfDraft)
    else:
        st.info("Press 'Start Draft' to begin.")
else:
    st.info("Please upload a player projection CSV file to start the simulation.")
