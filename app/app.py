import streamlit as st
from app.utils import (
    calculate_summary_stats,
    filter_dataset,
    generate_line_chart,
    get_top_bottom_countries,
    load_dataset,
)


def run():
    st.title('Inflation Rate Comparison Country Wise')

    df = load_dataset('Inflation_dataset.csv')
    if df.empty:
        return

    st.sidebar.title('Settings')
    selected_countries = st.sidebar.multiselect('Select Countries', df['Country'].unique())
    date_range = st.sidebar.slider(
        'Select Date Range',
        min_value=int(df['Year'].min()),
        max_value=int(df['Year'].max()),
        value=(int(df['Year'].min()), int(df['Year'].max()))
    )
    st.sidebar.markdown('---')

    st.write(
        'Compare inflation rates over time for chosen countries. '
        'Use the sidebar to select countries and the date range.'
    )

    if not selected_countries:
        st.warning('Please select at least one country for comparison.')
        return

    df_filtered = filter_dataset(df, selected_countries, date_range)

    if len(selected_countries) > 10:
        st.warning('Please select 10 or fewer countries for clearer visualization.')

    fig = generate_line_chart(df_filtered, 'Inflation Rate Over Time for Selected Countries')
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
        st.subheader('Highest Average Inflation by Country')
        st.table(highest)
        st.subheader('Lowest Average Inflation by Country')
        st.table(lowest)


if __name__ == '__main__':
    run()
