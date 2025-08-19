"""Transform HTMLs to tab-separated values file."""

# /// script
# requires-python = ">3.11,<3.14"
# dependencies = [
#     "pandas[html,parquet,xml]",
#     "polars",
# ]
# ///
from pathlib import Path

import pandas as pd
import polars as pl

PATH_TO_DATA: Path = Path("./data")

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

CHAMPIONS = {
    "2024-2025": "Liverpool",
    "2023-2024": "Manchester City",
    "2022-2023": "Manchester City",
    "2021-2022": "Manchester City",
    "2020-2021": "Manchester City",
    "2019-2020": "Liverpool",
    "2018-2019": "Manchester City",
    "2017-2018": "Manchester City",
    "2016-2017": "Chelsea",
    "2015-2016": "Leicester City",
    "2014-2015": "Chelsea",
    "2013-2014": "Manchester City",
    "2012-2013": "Manchester Utd",
    "2011-2012": "Manchester City",
    "2010-2011": "Manchester Utd",
    "2009-2010": "Chelsea",
    "2008-2009": "Manchester Utd",
    "2007-2008": "Manchester Utd",
    "2006-2007": "Manchester Utd",
    "2005-2006": "Chelsea",
    "2004-2005": "Chelsea",
    "2003-2004": "Arsenal",
    "2002-2003": "Manchester Utd",
    "2001-2002": "Arsenal",
    "2000-2001": "Manchester Utd",
    "1999-2000": "Manchester Utd",
    "1998-1999": "Manchester Utd",
    "1997-1998": "Arsenal",
    "1996-1997": "Manchester Utd",
    "1995-1996": "Manchester Utd",
    "1994-1995": "Blackburn",
    "1993-1994": "Manchester Utd",
    "1992-1993": "Manchester Utd",
}


def html_to_flat_dataframe(path_to_html: Path) -> pd.DataFrame:
    """Bring in a column-MultiIndex from HTML and make it single-level."""
    html_read = pd.read_html(
        path_to_html,
        flavor="lxml",
        dtype_backend="pyarrow",
        encoding="utf-8",
    )
    df: pd.DataFrame = html_read[0]
    if df.shape[1] == 37:
        df.columns = THIRTY_SEVEN_COLUMN_INDEX
    elif df.shape[1] == 25:
        df.columns = TWENTY_FIVE_COLUMN_INDEX
    else:
        _msg: str = (
            f"Unexpected number of columns, {len(df)}, "
            f"from file '{path_to_html.resolve()}'."
        )
        raise RuntimeError(_msg)

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
    if df.shape[1] == 25:
        subset: pd.DataFrame = df.loc[
            (df.loc[:, ("Demographics", "Age")].str.isnumeric())
            & (df[("Performance", "Gls")].str.isnumeric())
            & (df[("Performance", "Ast")].str.isnumeric()),
            pd.IndexSlice[
                ("Demographics", "Playing Time", "Performance"),
                desired_columns,
            ],
        ].copy()
    else:
        subset: pd.DataFrame = df.loc[
            :,
            pd.IndexSlice[
                ("Demographics", "Playing Time", "Performance"),
                desired_columns,
            ],
        ].copy()
    subset.columns = subset.columns.droplevel(0)
    subset["Age"] = subset["Age"].astype("int16[pyarrow]")
    subset["Min"] = subset["Min"].astype("int16[pyarrow]")
    subset["Gls"] = subset["Gls"].astype("int16[pyarrow]")
    subset["Ast"] = subset["Ast"].astype("int16[pyarrow]")

    return subset


def main() -> None:  # noqa:D103
    all_standings: list[pl.DataFrame] = [None] * len(CHAMPIONS)
    all_scorers: list[pl.DataFrame] = [None] * len(CHAMPIONS)

    for i, (szn, champ) in enumerate(CHAMPIONS.items()):
        # standings, GF, GA, Pts data from HTML
        _standings: pd.DataFrame = pd.read_html(
            io=PATH_TO_DATA / "premier-league" / f"standings_{szn}.html",
            flavor="lxml",
            dtype_backend="pyarrow",
            encoding="utf-8",
        )[0]
        _standings["s"] = szn
        df_standings: pl.DataFrame = _standings[
            ["s", "Rk", "Squad", "MP", "W", "D", "L", "GF", "GA", "Pts"]
        ]
        all_standings[i] = pl.from_pandas(df_standings).select(
            pl.col("s").alias("season"),
            pl.col("Rk").cast(pl.Int8).alias("standing"),
            pl.col("Squad").alias("squad"),
            pl.col("MP").cast(pl.Int8).alias("matches_played"),
            pl.col("W").cast(pl.Int8).alias("wins"),
            pl.col("D").cast(pl.Int8).alias("draws"),
            pl.col("L").cast(pl.Int8).alias("losses"),
            pl.col("GF").cast(pl.Int8).alias("goals_for"),
            pl.col("GA").cast(pl.Int8).alias("goals_against"),
            pl.col("Pts").cast(pl.Int8).alias("points"),
        )
        # players' scoring data from HTML
        _scoring: pl.DataFrame = pl.from_pandas(
            html_to_flat_dataframe(Path(f"data/premier-league/fbref_{szn}.html")),
        )
        all_scorers[i] = _scoring.with_columns(
            pl.lit(szn).alias("season"),
            pl.lit(champ).alias("champion"),
        )

    standings: pl.DataFrame = pl.concat(all_standings)
    scorers: pl.DataFrame = pl.concat(all_scorers)
    standings.join(
        scorers,
        how="full",
        left_on=["season", "squad"],
        right_on=["season", "Squad"],
        validate="1:m",
    ).drop(["season_right", "Squad"]).select(
        pl.col("season"),
        pl.col("champion"),
        pl.col("squad"),
        pl.col("standing"),
        pl.col("matches_played"),
        pl.col("points"),
        pl.col("wins"),
        pl.col("draws"),
        pl.col("losses"),
        pl.col("goals_for"),
        pl.col("goals_against"),
        pl.col("Player").alias("footballer"),
        pl.col("Min").alias("minutes_played"),
        pl.col("Gls").alias("goals"),
        pl.col("Ast").alias("assists"),
    ).with_columns(
        # can't just use the 'goals_for' because it includes opponents' own goals!
        pl.col("goals")
        .sum()
        .over(pl.col("season"), pl.col("squad"))
        .alias("squad_goals_no_own"),
        pl.col("goals")
        .truediv(pl.col("goals").sum().over(pl.col("season"), pl.col("squad")))
        .alias("prop_squad_goals_no_own")
        .cast(pl.Float32),
    ).sort(pl.col("prop_squad_goals_no_own"), descending=True).write_csv(
        Path("premier-league-data.tsv"),
        include_bom=True,
        include_header=True,
        separator="\t",
    )


if __name__ == "__main__":
    main()
