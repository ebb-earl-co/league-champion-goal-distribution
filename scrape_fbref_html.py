# /// script
# requires-python = ">3.11,<3.13"
# dependencies = [
#     "pandas[html,parquet,xml]",
#     "polars",
# ]
# ///

from pathlib import Path
import pandas as pd
import polars as pl


THIRTY_SEVEN_COLUMN_INDEX: tuple[tuple[str, str], ...] = (
    ("Demographics", "Rk"),
    ("Demographics", "Player"),
    ("Demographics", "Nation"),
    ("Demographics", "Pos"),
    ("Demographics", "Squad"),
    ("Demographics", "Age"),
    ("Demographics", "Born"),
    ("Playing Time", "MP"),
    ("Playing Time", "Starts"),
    ("Playing Time", "Min"),
    ("Playing Time", "90s"),
    ("Performance", "Gls"),
    ("Performance", "Ast"),
    ("Performance", "G+A"),
    ("Performance", "G-PK"),
    ("Performance", "PK"),
    ("Performance", "PKatt"),
    ("Performance", "CrdY"),
    ("Performance", "CrdR"),
    ("Expected", "xG"),
    ("Expected", "npxG"),
    ("Expected", "xAG"),
    ("Expected", "npxG+xAG"),
    ("Progression", "PrgC"),
    ("Progression", "PrgP"),
    ("Progression", "PrgR"),
    ("Per 90 Minutes", "Gls"),
    ("Per 90 Minutes", "Ast"),
    ("Per 90 Minutes", "G+A"),
    ("Per 90 Minutes", "G-PK"),
    ("Per 90 Minutes", "G+A-PK"),
    ("Per 90 Minutes", "xG"),
    ("Per 90 Minutes", "xAG"),
    ("Per 90 Minutes", "xG+xAG"),
    ("Per 90 Minutes", "npxG"),
    ("Per 90 Minutes", "npxG+xAG"),
    ("Matches", "hyperlink"),
)

TWENTY_FIVE_COLUMN_INDEX: tuple[tuple[str, str], ...] = (
    ("Demographics", "Rk"),
    ("Demographics", "Player"),
    ("Demographics", "Nation"),
    ("Demographics", "Pos"),
    ("Demographics", "Squad"),
    ("Demographics", "Age"),
    ("Demographics", "Born"),
    ("Playing Time", "MP"),
    ("Playing Time", "Starts"),
    ("Playing Time", "Min"),
    ("Playing Time", "90s"),
    ("Performance", "Gls"),
    ("Performance", "Ast"),
    ("Performance", "G+A"),
    ("Performance", "G-PK"),
    ("Performance", "PK"),
    ("Performance", "PKatt"),
    ("Performance", "CrdY"),
    ("Performance", "CrdR"),
    ("Per 90 Minutes", "Gls"),
    ("Per 90 Minutes", "Ast"),
    ("Per 90 Minutes", "G+A"),
    ("Per 90 Minutes", "G-PK"),
    ("Per 90 Minutes", "G+A-PK"),
    ("Matches", "hyperlink"),
)


def per_player_goal_proportion_of_total(
    df: pl.DataFrame, squad: str, column: str = "Gls"
) -> pl.DataFrame:
    subset = df.filter(pl.col("Squad") == squad)
    return subset.with_columns(
        pl.col(column).truediv(pl.col(column).sum()).alias("prop_total_goals")
    )


def subset_fbref_df_to_champions(path_to_html: Path, champ: str) -> pd.DataFrame:
    html_read = pd.read_html(
        path_to_html, flavor="lxml", dtype_backend="pyarrow", encoding="utf-8"
    )
    df: pd.DataFrame = html_read[0]
    # Just squad, player, and number of goals.
    # Copy isn't a terriby big deal here, as we have ~600 rows by 3 columns.
    subset = df.iloc[:, [4, 1, 11]].copy()
    cols = subset.columns.droplevel(0)
    subset.columns = cols

    to_return = (
        subset.loc[subset.iloc[:, 0].eq(champ), :]
        .drop(columns="Squad")
        .sort_values(by="Gls", ascending=False)
    )
    return to_return


def html_to_flat_dataframe(path_to_html: Path) -> pd.DataFrame:
    """The HTML will bring in a MultiIndex column; single-level index is desired."""
    html_read = pd.read_html(
        path_to_html, flavor="lxml", dtype_backend="pyarrow", encoding="utf-8"
    )
    df: pd.DataFrame = html_read[0]
    if df.shape[0] == 37:
        df.columns = THIRTY_SEVEN_COLUMN_INDEX
    elif df.shape[0] == 25:
        df.columns = TWENTY_FIVE_COLUMN_INDEX
    else:
        raise RuntimeError(
            f"Unexpected number of columns, {df.shape[0]}, from file '{path_to_html.resolve()}'."
        )

    desired_columns: list[str, str, str, str, str, str] = [
        "Squad",
        "Player",
        "Age",
        "Min",
        "Gls",
        "Ast",
    ]
    # If Age, Gls, or Ast value is a non-number string,
    # it's an HTML parsing artifact and is to be dropped
    subset: pd.DataFrame = df.loc[
        (df.loc[:, ("Demographics", "Age")].str.isnumeric())
        & (df[("Performance", "Gls")].str.isnumeric())
        & (df[("Performance", "Ast")].str.isnumeric()),
        pd.IndexSlice[
            ("Demographics", "Playing Time", "Performance"),
            desired_columns,
        ],
    ]
    subset.columns = subset.columns.droplevel(0)
    subset.loc[
        :,
        ["Age", "Min", "Gls", "Ast"]
    ] = subset.loc[
        :,
        ["Age", "Min", "Gls", "Ast"]
    ].astype("int16[pyarrow]")

    return subset


def main() -> None:
    s2425: Path = Path("fbref_premier_league_2024-2025_statistics.html")
    s2324: Path = Path("fbref_premier_league_2023-2024_statistics.html")
    s2223: Path = Path("fbref_premier_league_2022-2023_statistics.html")

    d2425: pd.DataFrame = subset_fbref_df_to_champions(
        path_to_html=s2425, champ="Liverpool"
    )
    d2425.to_csv(
        "fbref_goals_per_player_on_premier_league_champions_2024-2025.csv", index=False
    )

    d2324: pd.DataFrame = subset_fbref_df_to_champions(
        path_to_html=s2324, champ="Manchester City"
    )
    d2324.to_csv(
        "fbref_goals_per_player_on_premier_league_champions_2023-2024.csv", index=False
    )

    d2223: pd.DataFrame = subset_fbref_df_to_champions(
        path_to_html=s2223, champ="Manchester City"
    )
    d2223.to_csv(
        "fbref_goals_per_player_on_premier_league_champions_2022-2023.csv", index=False
    )


if __name__ == "__main__":
    main()
