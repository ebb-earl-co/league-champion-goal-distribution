# /// script
# requires-python = ">3.11,<3.13"
# dependencies = [
#     "pandas[html,parquet,xml]",
#     "polars",
# ]
# ///

from pathlib import Path

import pandas as pd

MULTI_INDEX_TUPLES: tuple[tuple[str, str], ...] = (
    (      'Demographics',       'Rk'),
    (      'Demographics',   'Player'),
    (      'Demographics',   'Nation'),
    (      'Demographics',      'Pos'),
    (      'Demographics',    'Squad'),
    (      'Demographics',      'Age'),
    (      'Demographics',     'Born'),
    (      'Playing Time',       'MP'),
    (      'Playing Time',   'Starts'),
    (      'Playing Time',      'Min'),
    (      'Playing Time',      '90s'),
    (       'Performance',      'Gls'),
    (       'Performance',      'Ast'),
    (       'Performance',      'G+A'),
    (       'Performance',     'G-PK'),
    (       'Performance',       'PK'),
    (       'Performance',    'PKatt'),
    (       'Performance',     'CrdY'),
    (       'Performance',     'CrdR'),
    (          'Expected',       'xG'),
    (          'Expected',     'npxG'),
    (          'Expected',      'xAG'),
    (          'Expected', 'npxG+xAG'),
    (       'Progression',     'PrgC'),
    (       'Progression',     'PrgP'),
    (       'Progression',     'PrgR'),
    (    'Per 90 Minutes',      'Gls'),
    (    'Per 90 Minutes',      'Ast'),
    (    'Per 90 Minutes',      'G+A'),
    (    'Per 90 Minutes',     'G-PK'),
    (    'Per 90 Minutes',   'G+A-PK'),
    (    'Per 90 Minutes',       'xG'),
    (    'Per 90 Minutes',      'xAG'),
    (    'Per 90 Minutes',   'xG+xAG'),
    (    'Per 90 Minutes',     'npxG'),
    (    'Per 90 Minutes', 'npxG+xAG')
)


def fix_table(path_to_html: Path, tuples=MULTI_INDEX_TUPLES) -> pd.DataFrame:
    """Repair the column MultiIndex parsed from HTML."""
    # read_html() gives us a length-one list
    df: pd.DataFrame = pd.read_html(
        path_to_html, flavor="lxml", dtype_backend="pyarrow", encoding="utf-8"
    )[0]

    # Drop the last column, just a hyperlink to the player's matches
    df: pd.DataFrame = df.iloc[:, :-1]

    # Fix the first seven columns that have an unnamed 0th index level
    df.columns = pd.MultiIndex.from_tuples(tuples)

    # TODO: change all integers to int16 to save memory

    return df


def main() -> None:
    for f in (p for p in Path().glob("*.html") if p.is_file() and p.stat().st_size > 0):
        d: pd.DataFrame = fix_table(f)
        d.to_csv(Path(f"{f.name}.csv"), index=False)
    
if __name__ == "__main__":
    main()
