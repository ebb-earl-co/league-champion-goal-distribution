for f in sorted(p for p in Path("data/la-liga").glob("*.html") if p.is_file() and p.stat().st_size > 0):
    try:
        df = pd.read_html(
            f,
            flavor="lxml",
            dtype_backend="pyarrow",
            encoding="utf-8",
        )[0]
    except:
        n_cols = None
    else:
        n_cols = df.shape[1]
    finally:
        print(
            f"{f.name}: {n_cols}"
        )
else:
    del df

def html_to_flat_dataframe(path_to_html: Path) -> pd.DataFrame:
    """The HTML will bring in a MultiIndex column; single-level index is desired."""
    html_read = pd.read_html(
        path_to_html, flavor="lxml", dtype_backend="pyarrow", encoding="utf-8"
    )
    df: pd.DataFrame = html_read[0]
    if df.shape[1] == 37:
        df.columns = THIRTY_SEVEN_COLUMN_INDEX
    elif df.shape[1] == 25:
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
    idx = pd.IndexSlice[("Demographics", "Playing Time", "Performance"), desired_columns]
    # If Age, Gls, or Ast value is a non-number string,
    # it's an HTML parsing artifact and is to be dropped
    # Actually, it suffices to check just the 0th column, Rk, for numeracy
    if df.shape[1] == 25:
        subset: pd.DataFrame = df.loc[df.iloc[:, 0].str.isnumeric(), idx].copy()
    else:
        subset: pd.DataFrame = df.loc[:, idx].copy()
    subset.columns = subset.columns.droplevel(0)
    subset["Age"] = subset["Age"].astype("int16[pyarrow]")
    subset["Min"] = subset["Min"].astype("int16[pyarrow]")
    subset["Gls"] = subset["Gls"].astype("int16[pyarrow]")
    subset["Ast"] = subset["Ast"].astype("int16[pyarrow]")
    return subset


premier_league_htmls = sorted(Path("data/premier-league").glob("fbref*.html"), key=lambda f: f.name)
la_liga_htmls = sorted(Path("data/la-liga").glob("*.html"), key=lambda f: f.name)

all_pl_seasons = [None for _ in iter(premier_league_htmls)]
all_ll_seasons = [None for _ in iter(la_liga_htmls)]

for i, p in enumerate(premier_league_htmls):
    season = p.name.split("_")[1].split(".")[0]
    pldf = pl.from_pandas(html_to_flat_dataframe(p))
    max_prop_goals_for_champ: pl.DataFrame = pldf.with_columns(
        pl.lit(season).alias("Season"),
        pl.col("Gls").sum().over(pl.col("Squad")).alias("total_goals").cast(pl.Int16),
        pl.col("Gls").truediv(pl.col("Gls").sum().over(pl.col("Squad"))).alias("prop_total_goals").cast(pl.Float32)
    ).sort(by="prop_total_goals", descending=True)
    all_pl_seasons[i] = max_prop_goals_for_champ

pl.concat(all_pl_seasons).select(
    "Season", "Squad", "Player", "Gls", "total_goals", "prop_total_goals"
).filter(
    pl.col("Gls").gt(0)
).sort(
    by="prop_total_goals", descending=True
)
