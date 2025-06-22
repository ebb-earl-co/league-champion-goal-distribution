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


def per_player_goal_proportion_of_total(df: pl.DataFrame, squad: str, column: str = "Gls") -> pl.DataFrame:
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
    subset = df.iloc[:, [4,1,11]].copy()
    cols = subset.columns.droplevel(0)
    subset.columns = cols

    to_return = subset.loc[
        subset.iloc[:, 0].eq(champ),
        :
    ].drop(columns="Squad").sort_values(by="Gls", ascending=False)
    return to_return


def main() -> None:
    s2425: Path = Path("fbref_premier_league_2024-2025_statistics.html")
    s2324: Path = Path("fbref_premier_league_2023-2024_statistics.html")
    s2223: Path = Path("fbref_premier_league_2022-2023_statistics.html")

    d2425: pd.DataFrame = subset_fbref_df_to_champions(
        path_to_html=s2425, champ="Liverpool"
    )
    d2425.to_csv(
        "fbref_goals_per_player_on_premier_league_champions_2024-2025.csv",
        index=False
    )

    d2324: pd.DataFrame = subset_fbref_df_to_champions(
        path_to_html=s2324, champ="Manchester City"
    )
    d2324.to_csv(
        "fbref_goals_per_player_on_premier_league_champions_2023-2024.csv",
        index=False
    )

    d2223: pd.DataFrame = subset_fbref_df_to_champions(
        path_to_html=s2223, champ="Manchester City"
    )
    d2223.to_csv(
        "fbref_goals_per_player_on_premier_league_champions_2022-2023.csv",
        index=False
    )

if __name__ == "__main__":
    main()
