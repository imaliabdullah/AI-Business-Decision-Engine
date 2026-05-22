import pandas as pd


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def format_percentage(value: float) -> str:
    return f"{value:.2f}%"


def dataframe_to_readable(df: pd.DataFrame) -> str:
    return df.to_string(index=False)
