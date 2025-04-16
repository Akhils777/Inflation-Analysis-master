import streamlit as st
import pandas as pd
import plotly.express as px

def generate_plotly_chart(df, selected_countries):
    filtered = df[df['Country'].isin(selected_countries)].copy()
    filtered['Inflation_rate'] = pd.to_numeric(filtered['Inflation_rate'], errors='coerce')
    filtered.dropna(subset=['Inflation_rate'], inplace=True)
    filtered.sort_values(by=['Country', 'Year'], inplace=True)

    fig = px.line(
        filtered,
        x='Year',
        y='Inflation_rate',
        color='Country',
        markers=True,
        title='Inflation Rate Over Time for Selected Countries'
    )
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Inflation Rate (%)',
        legend_title='Country',
        template='plotly_white',
        yaxis=dict(tickformat=".2f")
    )
    return fig

def calculate_summary_stats(df, selected_countries):
    selected_data = df[df['Country'].isin(selected_countries)].copy()
    selected_data['Inflation_rate'] = pd.to_numeric(selected_data['Inflation_rate'], errors='coerce')
    selected_data.dropna(subset=['Inflation_rate'], inplace=True)
    summary_stats = selected_data.groupby('Country')['Inflation_rate'].describe()
    return summary_stats

def run():
    st.title('Inflation Rate Comparison Country Wise')

    df = pd.read_csv(r'app\Inflation_dataset.csv', encoding='latin1')

    st.sidebar.title('Settings')
    selected_countries = st.sidebar.multiselect('Select Countries', df['Country'].unique())
    date_range = st.sidebar.slider(
        "Select Date Range",
        min_value=int(df['Year'].min()),
        max_value=int(df['Year'].max()),
        value=(int(df['Year'].min()), int(df['Year'].max()))
    )

    st.sidebar.markdown("---")

    st.write("""
    This app allows you to compare the inflation rate over time for selected countries. 
    Use the multiselect dropdown to choose countries and the slider to select the date range.
    """)

    df_filtered = df[(df['Country'].isin(selected_countries)) & (df['Year'].between(date_range[0], date_range[1]))]

    if selected_countries:
        if len(selected_countries) > 10:
            st.warning("Please select 10 or fewer countries for clearer visualization.")
        else:
            fig = generate_plotly_chart(df_filtered, selected_countries)
            st.plotly_chart(fig, use_container_width=True)

            summary_stats = calculate_summary_stats(df_filtered, selected_countries)
            st.subheader('Summary Statistics:')
            st.table(summary_stats)

            csv_data = summary_stats.to_csv().encode('utf-8')
        st.download_button(
            label="Download Summary Stats as CSV",
            data=csv_data,
            file_name='summary_stats.csv',
            mime='text/csv'
        )
    else:
        st.warning('Please select at least one country for comparison.')


if __name__ == "__main__":
    run()
