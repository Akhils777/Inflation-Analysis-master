from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_ROOT = Path(__file__).resolve().parent


@st.cache_data
def load_dataset(filename: str) -> pd.DataFrame:
    path = APP_ROOT / filename
    try:
        df = pd.read_csv(path, encoding='latin1')
    except FileNotFoundError:
        st.error(f"Dataset file not found: {filename}")
        return pd.DataFrame(columns=['Year', 'Country', 'Inflation_rate'])
    except Exception as exc:
        st.error(f"Unable to load dataset {filename}: {exc}")
        return pd.DataFrame(columns=['Year', 'Country', 'Inflation_rate'])

    if not {'Year', 'Country', 'Inflation_rate'}.issubset(df.columns):
        st.error(f"Dataset {filename} must contain Year, Country, and Inflation_rate columns.")
        return pd.DataFrame(columns=['Year', 'Country', 'Inflation_rate'])

    return clean_dataset(df)


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    duplicate_header_mask = (
        df['Year'].astype(str).str.strip().eq('Year') &
        df['Country'].astype(str).str.strip().eq('Country') &
        df['Inflation_rate'].astype(str).str.strip().eq('Inflation_rate')
    )
    if duplicate_header_mask.any():
        df = df.loc[~duplicate_header_mask]

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['Inflation_rate'] = pd.to_numeric(df['Inflation_rate'], errors='coerce')
    df = df.dropna(subset=['Year', 'Country', 'Inflation_rate'])
    df['Year'] = df['Year'].astype(int)
    return df


def filter_dataset(df: pd.DataFrame, selected_countries: list, date_range: tuple) -> pd.DataFrame:
    if df.empty or not selected_countries:
        return df.iloc[0:0]
    return df[df['Country'].isin(selected_countries) & df['Year'].between(*date_range)].copy()


def calculate_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return df.groupby('Country')['Inflation_rate'].describe()


def get_top_bottom_countries(df: pd.DataFrame, n: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    average_inflation = df.groupby('Country')['Inflation_rate'].mean().sort_values()
    lowest = average_inflation.head(n).reset_index(name='Average Inflation (%)')
    highest = average_inflation.tail(n).sort_values(ascending=False).reset_index(name='Average Inflation (%)')
    return highest, lowest


def generate_line_chart(df: pd.DataFrame, title: str) -> px.line:
    fig = px.line(
        df,
        x='Year',
        y='Inflation_rate',
        color='Country',
        markers=True,
        title=title
    )
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Inflation Rate (%)',
        legend_title='Country',
        template='plotly_white'
    )
    return fig


def generate_bar_chart(df: pd.DataFrame, title: str) -> px.bar:
    fig = px.bar(
        df,
        x='Year',
        y='Inflation_rate',
        color='Country',
        barmode='group',
        title=title,
        labels={'Inflation_rate': 'Inflation Rate (%)'},
        height=600
    )
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Inflation Rate (%)',
        legend_title='Country',
        template='plotly_white',
        bargap=0.2
    )
    return fig
