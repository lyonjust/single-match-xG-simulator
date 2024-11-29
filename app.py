import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import matplotlib as mpl
import matplotlib.pyplot as plt
import requests
import io
import urllib.parse

from functions import simulate

# TODO
# fix fotmob score at end of 90 mins (e.g. WC final 3370572)
# dynamic subplot ratios depending on whether tickboxes selected
# show team names highlighted, not "Home team wins in"

N_SIMS = 100000
SEED = 0

rng = np.random.default_rng(SEED)

mpl.rcParams["figure.dpi"] = 300

st.set_page_config(page_title="xG simulator", page_icon="⚽")

streamlit_app_url = "https://single-match-xg-simulator.streamlit.app"

st.title("Single match xG simulator")

st.write("App built by [Justin Lyons](https://github.com/lyonjust)")

caption = (
    "This app takes a given number of xG values for a football match and performs "
    + f"{N_SIMS:,}"
    + " random simulations of the match based on the outcome of each shot attempt.\n\n"
)
caption = caption + "It then provides a summary of the possible match outcomes.\n\n"
caption = (
    caption
    + "The purpose is to reinforce understanding and improve language around xG, "
)
caption = (
    caption
    + "as well as highlight the limitations of drawing absolute conclusions from just the overall aggregate single match xG comparison.\n\n"
)
caption = (
    caption
    + "If you choose a **custom match**, you can enter any sequence of custom xG values for a hypothetical home and away team, as well as a hypothetical match result.\n\n"
)
# caption = (
#     caption
#     + 'If you choose a **FotMob match ID**, you can enter a valid match ID from FotMob (e.g. "3854572") and the app will perform the simulation based on the shot details recorded for this match. Penalty shootouts are excluded from these analyses.\n'
# )

fotmob_helper = '\nFotMob match IDs are the digits after the hash ("#") at the very end of the match details URL: fotmob.com/matches/<home_team>-vs-<away_team>/<alpha_id>#***<match_id>***'
# caption = caption + fotmob_helper

with st.expander("Click here for an explanation of how to use this app"):
    st.write(caption)

custom_or_understat_or_fotmob = st.radio(
    "Simulate a...", ("FotMob match ID", "Custom match")
)  # 'Understat match ID',

st.header("Input")

input_flag = False

if custom_or_understat_or_fotmob == "Custom match":
    input_flag = True

    st.caption(
        "Please enter the xG of each team's shots in the input boxes below.\n\nIndividual xG values should be separated by a comma (',')"
    )

    default_value_home_shots_string = "0.8"
    default_value_away_shots_string = away_shots_xg = "0.2, 0.2, 0.2, 0.2"

    home_shots = st.text_input("Home shots xG", value=default_value_home_shots_string)
    away_shots = st.text_input("Away shots xG", value=default_value_away_shots_string)

    home_team_observed_goals = st.number_input(
        "Home team actual goals scored", min_value=0, step=1, value=0
    )
    away_team_observed_goals = st.number_input(
        "Away team actual goals scored", min_value=0, step=1, value=1
    )

    home_xg = simulate.xg_to_array(home_shots)
    away_xg = simulate.xg_to_array(away_shots)

    total_home_xg = sum(home_xg)
    total_away_xg = sum(away_xg)

    home_goals = simulate.simulate_chances(rng, N_SIMS, home_xg)
    away_goals = simulate.simulate_chances(rng, N_SIMS, away_xg)
    home_margin = home_goals - away_goals

    match_date = None
    home_team_name = "Home team"
    away_team_name = "Away team"
    extra_plot_comment = ""
    source = None

    df_match_outcomes = simulate.get_match_outcomes(home_goals, away_goals, home_margin)

    (
        simulated_home_win_percent,
        simulated_away_win_percent,
        simulated_draw_percent,
        percentage_of_sims_matching_actual_score,
    ) = simulate.get_sims_matching_score(
        df_match_outcomes, home_team_observed_goals, away_team_observed_goals
    )

else:  # fotmob
    #     fotmob_caption = "Please enter the match ID of an FotMob match, e.g. 3854572"
    #     fotmob_caption = fotmob_caption + "\n\n" + fotmob_helper
    fotmob_caption = "Unfortunately, in November 2024 FotMob enforced additional restrictions on their API, rendering this app broken until further notice."
    st.caption(fotmob_caption)

    # fotmob_match_id = st.text_input("FotMob match ID").strip()
    fotmob_match_id = None

    # cater for teams with no shots?

    url_base = "https://www.fotmob.com/api/"
    url_match_details = "matchDetails?matchId="

    if fotmob_match_id:
        if not fotmob_match_id.isdigit():
            st.write("A FotMob match ID must only contain numbers. Please try again.")

        else:
            input_flag = True

            url_complete = url_base + url_match_details + fotmob_match_id

            match_summary = requests.get(url_complete).json()

            if not match_summary["general"]["homeTeam"]["id"]:
                st.write(
                    "Sorry, match ID "
                    + fotmob_match_id
                    + " does not exist in the FotMob database. Please try again."
                )
                input_flag = False

            else:
                shot_summary = match_summary["content"]["shotmap"]["shots"]

                match_date = pd.to_datetime(
                    match_summary["general"]["matchTimeUTCDate"]
                )

                home_team_name = match_summary["general"]["homeTeam"]["name"]
                home_team_id = match_summary["general"]["homeTeam"]["id"]

                away_team_name = match_summary["general"]["awayTeam"]["name"]
                away_team_id = match_summary["general"]["awayTeam"]["id"]

                home_goals_actual = [
                    team["score"]
                    for team in match_summary["header"]["teams"]
                    if team["id"] == home_team_id
                ][0]
                away_goals_actual = [
                    team["score"]
                    for team in match_summary["header"]["teams"]
                    if team["id"] == away_team_id
                ][0]

                st.header(home_team_name + " v " + away_team_name)

                if len(shot_summary) == 0:
                    st.write(
                        "Sorry, FotMob does not track shots for this match. Please try another match ID."
                    )
                    input_flag = False
                else:
                    source = "fotmob"

                    shot_summary_no_shootout = [
                        shot
                        for shot in shot_summary
                        if shot["period"] != "PenaltyShootout"
                    ]

                    shots_in_extra_time = [
                        shot
                        for shot in shot_summary
                        if shot["period"] in ["FirstHalfExtra", "SecondHalfExtra"]
                    ]

                    extra_plot_comment = ""

                    simulate_result_90_mins_only = False
                    if shots_in_extra_time:
                        simulate_result_90_mins_only = st.checkbox(
                            "Simulate result at end of 90 minutes (i.e. ignore extra time)",
                            value=False,
                        )

                    if simulate_result_90_mins_only:
                        shot_summary_no_shootout = [
                            shot
                            for shot in shot_summary_no_shootout
                            if shot["period"] in ["FirstHalf", "SecondHalf"]
                        ]

                        extra_plot_comment += (
                            "Result simulated to end of 90 minutes regulation time\n"
                        )

                    penalties_not_in_shootout = [
                        shot
                        for shot in shot_summary
                        if shot["situation"] == "Penalty"
                        and shot["period"] != "PenaltyShootout"
                    ]

                    exclude_penalties = False
                    if penalties_not_in_shootout:
                        exclude_penalties = st.checkbox(
                            "Exclude penalties awarded (i.e. simulate NPxG)",
                            value=False,
                        )

                    if exclude_penalties:
                        shot_summary_no_shootout = [
                            shot
                            for shot in shot_summary_no_shootout
                            if shot["situation"] != "Penalty"
                        ]

                        extra_plot_comment += (
                            "Simulations based on non-penalty xG (NPxG) only"
                        )

                    home_shots_list = [
                        [
                            shot["min"],
                            shot["playerName"],
                            shot["situation"],
                            shot["expectedGoals"],
                            shot["eventType"],
                        ]
                        for shot in shot_summary_no_shootout
                        if shot["teamId"] == home_team_id
                    ]
                    away_shots_list = [
                        [
                            shot["min"],
                            shot["playerName"],
                            shot["situation"],
                            shot["expectedGoals"],
                            shot["eventType"],
                        ]
                        for shot in shot_summary_no_shootout
                        if shot["teamId"] == away_team_id
                    ]

                    columns = ["Minute", "Player", "Situation", "xG", "Outcome"]

                    df_home_shots = pd.DataFrame(home_shots_list, columns=columns)
                    df_away_shots = pd.DataFrame(away_shots_list, columns=columns)

                    total_home_xg = df_home_shots["xG"].sum()
                    total_away_xg = df_away_shots["xG"].sum()

                    home_goals = simulate.simulate_chances(
                        rng, N_SIMS, df_home_shots["xG"]
                    )
                    away_goals = simulate.simulate_chances(
                        rng, N_SIMS, df_away_shots["xG"]
                    )
                    home_margin = home_goals - away_goals

                    df_match_outcomes = simulate.get_match_outcomes(
                        home_goals, away_goals, home_margin
                    )

                    home_team_observed_goals = int(home_goals_actual)
                    away_team_observed_goals = int(away_goals_actual)

                    (
                        simulated_home_win_percent,
                        simulated_away_win_percent,
                        simulated_draw_percent,
                        percentage_of_sims_matching_actual_score,
                    ) = simulate.get_sims_matching_score(
                        df_match_outcomes,
                        home_team_observed_goals,
                        away_team_observed_goals,
                    )

                    st.header("Shot details")

                    st.subheader(home_team_name + " (home)")

                    st.dataframe(df_home_shots)

                    st.subheader(away_team_name + " (away)")

                    st.dataframe(df_away_shots)

if input_flag:
    st.header("Match outcomes")

    img = io.BytesIO()

    fig, ax, plot_title = simulate.plot_margins(
        df_match_outcomes,
        home_team_observed_goals,
        away_team_observed_goals,
        simulated_home_win_percent,
        simulated_draw_percent,
        simulated_away_win_percent,
        percentage_of_sims_matching_actual_score,
        total_home_xg,
        total_away_xg,
        match_date=match_date,
        home_team=home_team_name,
        away_team=away_team_name,
        extra_plot_comment=extra_plot_comment,
        io=img,
        source=source,
        app_url=streamlit_app_url,
    )

    st.pyplot(fig=fig)

    file_name = "simulated_xg.png"

    btn = st.download_button(
        label="Download plot of simulated match outcomes",
        data=img,
        file_name=file_name,
        mime="image/png",
    )

    # data-related="lyonjust"
    # data-via="lyonjust"
    # data-hashtags="xg_simulator"

    components.html(
        '''
        <a href="https://twitter.com/intent/tweet" class="twitter-share-button" 
        data-text="'''
        + plot_title
        + """"
        data-url="""
        + streamlit_app_url
        + """
        data-size="large" 
        >
        Tweet
        </a>
        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    """
    )

    fig, ax = simulate.plot_exact_scores(df_match_outcomes)

    st.pyplot(fig=fig)
