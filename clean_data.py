from pathlib import Path

import pandas as pd

APP_ROOT = Path(__file__).resolve().parent
RAW_DIR = APP_ROOT / 'app'
CLEAN_SUFFIX = '_cleaned'
FILES = [
    'Inflation_dataset.csv',
    'covid_dataset.csv',
    'Continental_dataset.csv',
    'War_dataset.csv',
]


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    duplicate_header_mask = (
        df['Year'].astype(str).str.strip().eq('Year') &
        df['Country'].astype(str).str.strip().eq('Country') &
        df['Inflation_rate'].astype(str).str.strip().eq('Inflation_rate')
    )
    df = df.loc[~duplicate_header_mask]

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['Inflation_rate'] = pd.to_numeric(df['Inflation_rate'], errors='coerce')
    df = df.dropna(subset=['Year', 'Country', 'Inflation_rate'])
    df['Year'] = df['Year'].astype(int)
    return df


def clean_file(filename: str) -> None:
    path = RAW_DIR / filename
    cleaned_path = RAW_DIR / f"{path.stem}{CLEAN_SUFFIX}{path.suffix}"
    print(f'Cleaning {path.name} -> {cleaned_path.name}')

    df = pd.read_csv(path, encoding='latin1')
    cleaned = clean_dataset(df)
    cleaned.to_csv(cleaned_path, index=False, encoding='utf-8')
    print(f'  rows before: {len(df)}')
    print(f'  rows after : {len(cleaned)}')


if __name__ == '__main__':
    for filename in FILES:
        clean_file(filename)
