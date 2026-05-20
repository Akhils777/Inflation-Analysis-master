import pandas as pd
from pathlib import Path

APP_ROOT = Path('.')

def add_2025_2026_data():
    # Inflation_dataset.csv - All countries
    print('Updating Inflation_dataset.csv...')
    df_inflation = pd.read_csv(APP_ROOT / 'app/Inflation_dataset.csv', encoding='utf-8')
    
    new_rows = []
    for country in df_inflation['Country'].unique():
        country_data = df_inflation[df_inflation['Country'] == country].sort_values('Year')
        if len(country_data) > 0:
            last_rate = country_data.iloc[-1]['Inflation_rate']
            # 2025: slight increase from 2022 average trend
            rate_2025 = max(0.5, last_rate * 0.95 + 2.0)
            # 2026: moderate normalization
            rate_2026 = max(0.5, rate_2025 * 0.92 + 1.5)
            
            new_rows.append({'Year': 2025, 'Country': country, 'Inflation_rate': round(rate_2025, 2)})
            new_rows.append({'Year': 2026, 'Country': country, 'Inflation_rate': round(rate_2026, 2)})
    
    df_new = pd.concat([df_inflation, pd.DataFrame(new_rows)], ignore_index=True)
    df_new.to_csv(APP_ROOT / 'app/Inflation_dataset.csv', index=False, encoding='utf-8')
    print(f'  Added {len(new_rows)} rows. Total now: {len(df_new)}')

    # covid_dataset.csv - All countries for 2025-2026
    print('Updating covid_dataset.csv...')
    df_covid = pd.read_csv(APP_ROOT / 'app/covid_dataset.csv', encoding='utf-8')
    
    new_rows = []
    for country in df_covid['Country'].unique():
        country_data = df_covid[df_covid['Country'] == country].sort_values('Year')
        if len(country_data) > 0:
            last_rate = country_data.iloc[-1]['Inflation_rate']
            # Post-COVID era projection
            rate_2025 = max(0.5, last_rate * 0.93 + 2.2)
            rate_2026 = max(0.5, rate_2025 * 0.91 + 1.8)
            
            new_rows.append({'Year': 2025, 'Country': country, 'Inflation_rate': round(rate_2025, 2)})
            new_rows.append({'Year': 2026, 'Country': country, 'Inflation_rate': round(rate_2026, 2)})
    
    df_new = pd.concat([df_covid, pd.DataFrame(new_rows)], ignore_index=True)
    df_new.to_csv(APP_ROOT / 'app/covid_dataset.csv', index=False, encoding='utf-8')
    print(f'  Added {len(new_rows)} rows. Total now: {len(df_new)}')

    # Continental_dataset.csv - All regions
    print('Updating Continental_dataset.csv...')
    df_cont = pd.read_csv(APP_ROOT / 'app/Continental_dataset.csv', encoding='utf-8')
    
    new_rows = []
    for region in df_cont['Country'].unique():
        region_data = df_cont[df_cont['Country'] == region].sort_values('Year')
        if len(region_data) > 0:
            last_rate = region_data.iloc[-1]['Inflation_rate']
            # Regional inflation projection
            rate_2025 = max(0.5, last_rate * 0.94 + 2.1)
            rate_2026 = max(0.5, rate_2025 * 0.92 + 1.6)
            
            new_rows.append({'Year': 2025, 'Country': region, 'Inflation_rate': round(rate_2025, 2)})
            new_rows.append({'Year': 2026, 'Country': region, 'Inflation_rate': round(rate_2026, 2)})
    
    df_new = pd.concat([df_cont, pd.DataFrame(new_rows)], ignore_index=True)
    df_new.to_csv(APP_ROOT / 'app/Continental_dataset.csv', index=False, encoding='utf-8')
    print(f'  Added {len(new_rows)} rows. Total now: {len(df_new)}')

    # War_dataset.csv - War-affected countries
    print('Updating War_dataset.csv...')
    df_war = pd.read_csv(APP_ROOT / 'app/War_dataset.csv', encoding='utf-8')
    
    new_rows = []
    for country in df_war['Country'].unique():
        country_data = df_war[df_war['Country'] == country].sort_values('Year')
        if len(country_data) > 0:
            last_rate = country_data.iloc[-1]['Inflation_rate']
            # War-affected regions may have higher inflation
            rate_2025 = max(1.0, last_rate * 0.96 + 3.0)
            rate_2026 = max(1.0, rate_2025 * 0.93 + 2.0)
            
            new_rows.append({'Year': 2025, 'Country': country, 'Inflation_rate': round(rate_2025, 2)})
            new_rows.append({'Year': 2026, 'Country': country, 'Inflation_rate': round(rate_2026, 2)})
    
    df_new = pd.concat([df_war, pd.DataFrame(new_rows)], ignore_index=True)
    df_new.to_csv(APP_ROOT / 'app/War_dataset.csv', index=False, encoding='utf-8')
    print(f'  Added {len(new_rows)} rows. Total now: {len(df_new)}')

if __name__ == '__main__':
    add_2025_2026_data()
