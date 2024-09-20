# apps/app1.py
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def generate_plot(df, selected_countries):
    # Plotting using Seaborn (Line plot with markers for selected countries)
    plt.figure(figsize=(12, 8))

    for country in selected_countries:
        country_data = df[df['Country'] == country]
        sns.lineplot(x='Year', y='Inflation_rate', data=country_data, label=country, marker='o', markersize=8)

    plt.title('Inflation Rate Over Time for Selected Countries with Markers')
    plt.xlabel('Year')
    plt.ylabel('Inflation Rate')
    plt.legend(loc='upper right')

    # Save the plot to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Encode the plot image to base64
    plot_url = base64.b64encode(img.getvalue()).decode()

    return plot_url

def calculate_summary_stats(df, selected_countries):
    selected_data = df[df['Country'].isin(selected_countries)]
    summary_stats = selected_data.groupby('Country')['Inflation_rate'].describe()
    return summary_stats

def run1():
    st.title('Inflation Rate Comparison During Covid')

    df = pd.read_csv(r'app\covid_dataset.csv', encoding='latin1')

    st.sidebar.title('Settings')
    selected_countries = st.sidebar.multiselect('Select Countries', df['Country'].unique())
    date_range = st.sidebar.slider("Select Date Range", min_value=df['Year'].min(), max_value=df['Year'].max(), value=(df['Year'].min(), df['Year'].max()))

    st.sidebar.markdown("---")

    st.write("""
    This app allows you to compare the inflation rate over time for selected countries. 
    Use the multiselect dropdown to choose countries and the slider to select the date range.
    """)

    df_filtered = df[(df['Country'].isin(selected_countries)) & (df['Year'].between(date_range[0], date_range[1]))]

    if selected_countries:
        plot_url = generate_plot(df_filtered, selected_countries)

        st.image(f"data:image/png;base64,{plot_url}", use_column_width=True, caption='Inflation Rate Over Time for Selected Countries with Markers')

        summary_stats = calculate_summary_stats(df_filtered, selected_countries)

        st.subheader('Summary Statistics:')
        st.table(summary_stats)
    else:
        st.warning('Please select at least one country for comparison.')