import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from highlight_text import fig_text

N_SIMS = 100000
SEED = 0

rng = np.random.default_rng(SEED)

outcome_colours = {"Home win": "#1c7ed6", "Draw": "#495057", "Away win": "#d6336c"}


def simulate_chances(rng, number_of_sims, xg_of_chances):
    """
    Simulates goals scored given a list of xG chances
    Returns a 1D array of size number_of_sims with each element being the goals scored in that simulation
    """

    goals_scored = np.zeros(number_of_sims)

    for i in range(number_of_sims):
        for shot_xg in xg_of_chances:
            random = rng.random()
            if shot_xg >= random:
                outcome = 1
            else:
                outcome = 0
            goals_scored[i] = goals_scored[i] + outcome

    return goals_scored


def StringRepresentsFloat(s):
    try:
        float(s)
        return str(float(s)) == s
    except ValueError:
        return False


def xg_to_array(xg_string):
    trimmed_array = [x.strip() for x in xg_string.split(",")]
    # handle case where extra trailing comma is included
    xg_array = [
        float(trimmed_x)
        for trimmed_x in trimmed_array
        if StringRepresentsFloat(trimmed_x) and 0 < float(trimmed_x) < 1
    ]
    return xg_array


def get_match_outcomes(home_goals, away_goals, home_margin):
    match_outcomes = np.vstack((home_goals, away_goals, home_margin))

    df_match_outcomes = pd.DataFrame(
        match_outcomes.T, columns=["home_goals", "away_goals", "home_margin"]
    )

    for column in ["home_goals", "away_goals", "home_margin"]:
        df_match_outcomes[column] = df_match_outcomes[column].astype(int)

    conditions = [
        df_match_outcomes["home_margin"] > 0,
        df_match_outcomes["home_margin"] < 0,
    ]

    choices = ["Home win", "Away win"]

    df_match_outcomes["match_outcome"] = np.select(
        condlist=conditions, choicelist=choices, default="Draw"
    )

    df_match_outcomes["final_score"] = (
        df_match_outcomes["home_goals"].apply(str)
        + " - "
        + df_match_outcomes["away_goals"].apply(str)
    )

    return df_match_outcomes


def get_sims_matching_score(
    df_match_outcomes, home_team_observed_goals, away_team_observed_goals
):
    number_of_sims_matching_actual_score = len(
        df_match_outcomes[
            (df_match_outcomes["home_goals"] == home_team_observed_goals)
            & (df_match_outcomes["away_goals"] == away_team_observed_goals)
        ]
    )
    percentage_of_sims_matching_actual_score = (
        number_of_sims_matching_actual_score / N_SIMS
    )

    df_grouped = (
        df_match_outcomes[["match_outcome", "home_goals"]]
        .groupby("match_outcome")
        .count()
    )
    df_grouped.columns = ["count"]
    df_grouped = df_grouped.reindex(["Home win", "Draw", "Away win"])

    df_grouped["proportion"] = df_grouped["count"] / df_grouped["count"].sum()

    df_grouped["percentage"] = (
        df_grouped["proportion"].astype(float).map("{:.1%}".format)
    )

    df_grouped = df_grouped[["percentage"]]

    simulated_home_win_percent = df_grouped.loc["Home win", "percentage"]
    simulated_away_win_percent = df_grouped.loc["Away win", "percentage"]
    simulated_draw_percent = df_grouped.loc["Draw", "percentage"]

    return (
        simulated_home_win_percent,
        simulated_away_win_percent,
        simulated_draw_percent,
        percentage_of_sims_matching_actual_score,
    )


def plot_margins(
    df_match_outcomes,
    home_team_observed_goals,
    away_team_observed_goals,
    simulated_home_win_percent,
    simulated_draw_percent,
    simulated_away_win_percent,
    percentage_of_sims_matching_actual_score,
    total_home_xg,
    total_away_xg,
    match_date=None,
    home_team="Home team",
    away_team="Away team",
    extra_plot_comment="",
    io=None,
    source=None,
    app_url=None,
):
    fig, ax = plt.subplots(nrows=3, figsize=(8, 8), height_ratios=[8.5, 12, 3.5])

    sns.histplot(
        data=df_match_outcomes,
        x="home_margin",
        discrete=True,
        stat="density",
        hue="match_outcome",
        palette=outcome_colours,
        ax=ax[1],
        zorder=1,
        alpha=1,
        legend=False,
    )

    ax[0].set_axis_off()
    ax[2].set_axis_off()

    ax[1].spines["top"].set_visible(False)
    ax[1].spines["right"].set_visible(False)
    ax[1].set_ylabel("Percent of Simulations")  # , rotation=0)
    ax[1].set_xlabel("Full Time Margin (Home Team Goals - Away Team Goals)")

    ax[1].yaxis.set_major_formatter(mtick.PercentFormatter(1, 0))

    plot_title = (
        home_team
        + " (home) "
        + f"{total_home_xg:.2f}"
        + " xG - "
        + away_team
        + " (away) "
        + f"{total_away_xg:.2f}"
        + " xG"
    )

    if match_date:
        date_str = "\n" + f"{match_date:%d %B %Y}" + "\n"
    else:
        date_str = "\n"

    title = fig_text(
        x=0.12,
        y=0.9,
        s="<"
        + plot_title
        + ">"
        + date_str
        + "\n\nActual outcome: "
        + home_team
        + " "
        + f"{home_team_observed_goals:.0f}"
        + " - "
        + away_team
        + " "
        + f"{away_team_observed_goals:.0f}"
        + "\n\n<Home team wins> in "
        + simulated_home_win_percent
        + " of simulations\n<Away team wins> in "
        + simulated_away_win_percent
        + " of simulations\n<Match is drawn> in "
        + simulated_draw_percent
        + " of simulations\nExact scoreline observed in "
        + f"{percentage_of_sims_matching_actual_score:.1%}"
        + " simulations\n\n"
        + extra_plot_comment,
        fontsize=14,
        highlight_textprops=[
            {"weight": "bold"},
            {"color": outcome_colours["Home win"], "weight": "bold"},
            {"color": outcome_colours["Away win"], "weight": "bold"},
            {"color": outcome_colours["Draw"], "weight": "bold"},
        ],
    )

    text_areas = [t for i, t in enumerate(title.text_areas) if i != 1]

    text_areas = [t.get_text() for t in text_areas]

    text_areas.insert(1, "\n\n")
    text_areas.insert(3, "\n\n")
    text_areas.insert(6, "\n")
    text_areas.insert(9, "\n")
    text_areas.insert(12, "\n")

    title_string = "".join(text_areas)
    title_string = title_string.replace(" (home)", "")
    title_string = title_string.replace(" (away)", "")
    title_string = title_string.replace(" of simulations", "")

    title_string = title_string + "\n\n"

    footer_text = app_url
    footer_text = footer_text + "\nBuilt by @lyonjust"

    if source == "fotmob":
        footer_text = footer_text + "\nData courtesy of FotMob"

    ax[2].text(
        x=0.99, y=0, s=footer_text, horizontalalignment="right", fontstyle="italic"
    )

    fig.tight_layout()

    fig.savefig(io, format="png")

    return fig, ax, title_string


def plot_exact_scores(df_match_outcomes):
    df_possible_scores = (
        df_match_outcomes[["final_score", "home_margin", "home_goals", "match_outcome"]]
        .groupby(["final_score", "home_margin", "match_outcome"])
        .count()
        .reset_index()
        .sort_values("home_goals", ascending=False)
    )
    df_possible_scores.columns = [
        "final_score",
        "home_margin",
        "match_outcome",
        "simulations",
    ]
    df_possible_scores["percent"] = df_possible_scores["simulations"] / N_SIMS

    fig_y_length = len(df_possible_scores) / 4

    fig, ax = plt.subplots(figsize=(5, fig_y_length))

    g = sns.barplot(
        data=df_possible_scores,
        y="final_score",
        x="percent",
        hue="match_outcome",
        palette=outcome_colours,
        ax=ax,
        dodge=False,
        alpha=1,
    )
    g.legend_.remove()
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1, 0))

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(
        axis="y",  # changes apply to the y-axis
        which="both",  # both major and minor ticks are affected
        left=False,
    )
    ax.set_ylabel("Match Score\n(Home Team - Away Team)")  # , rotation=0)
    ax.set_xlabel("Percent of Simulations")

    return fig, ax
