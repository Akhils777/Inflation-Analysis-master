import streamlit as st
from app.utils import (
    calculate_summary_stats,
    filter_dataset,
    generate_bar_chart,
    get_top_bottom_countries,
    load_dataset,
)


def run1():
    st.title('Inflation Rate Comparison During Covid')

    df = load_dataset('covid_dataset.csv')
    if df.empty:
        return

    st.sidebar.title('Settings')
    country_options = df['Country'].unique()
    default_countries = list(country_options[:3])
    selected_countries = st.sidebar.multiselect(
        'Select Countries', options=country_options, default=default_countries
    )

    date_range = st.sidebar.slider(
        'Select Date Range',
        min_value=int(df['Year'].min()),
        max_value=int(df['Year'].max()),
        value=(int(df['Year'].min()), int(df['Year'].max()))
    )
    st.sidebar.markdown('---')

    st.write(
        'Compare inflation rates during the COVID period by country. '
        'Choose countries and date range in the sidebar.'
    )

    if not selected_countries:
        st.warning('Please select at least one country for comparison.')
        return

    df_filtered = filter_dataset(df, selected_countries, date_range)
    fig = generate_bar_chart(df_filtered, 'COVID-Era Inflation Rate Comparison')
    st.plotly_chart(fig, use_container_width=True)

    summary_stats = calculate_summary_stats(df_filtered)
    if not summary_stats.empty:
        st.subheader('Summary Statistics')
        st.table(summary_stats)

        csv_data = summary_stats.to_csv().encode('utf-8')
        st.download_button(
            label='Download Summary Stats as CSV',
            data=csv_data,
            file_name='summary_stats.csv',
            mime='text/csv'
        )

    highest, lowest = get_top_bottom_countries(df_filtered)
    if not highest.empty:
        st.subheader('Highest Average COVID Inflation by Country')
        st.table(highest)
        st.subheader('Lowest Average COVID Inflation by Country')
        st.table(lowest)
