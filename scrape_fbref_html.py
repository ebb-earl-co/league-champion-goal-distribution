# /// script
# requires-python = "==3.12"
# dependencies = [
#     "pandas[html,parquet,performance,xml]",
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


def main() -> None:
    p = Path("fbref_premier_league_2024-2025_statistics.html")
    df = pd.read_html(p)[0]
    # Just squad, player, and number of goals
    subset = df.iloc[:, [4,1,11]].copy()
    subset.loc[:, "Champion"] = "Liverpool"
    subset.loc[:, "Season"] = "2024-2025"
    subset.to_csv("fbref_goals_per_player_premier_league_2024-2025.csv.gz", compression="gzip")

if __name__ == "__main__":
    main()
