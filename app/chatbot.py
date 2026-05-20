import pandas as pd
from pathlib import Path
from difflib import get_close_matches
import plotly.express as px

APP_ROOT = Path(__file__).resolve().parent


class InflationChatbot:
    """Chatbot for answering questions about inflation data."""

    def __init__(self):
        self.inflation_df = pd.read_csv(APP_ROOT / 'Inflation_dataset.csv', encoding='utf-8')
        self.covid_df = pd.read_csv(APP_ROOT / 'covid_dataset.csv', encoding='utf-8')
        self.continental_df = pd.read_csv(APP_ROOT / 'Continental_dataset.csv', encoding='utf-8')
        self.war_df = pd.read_csv(APP_ROOT / 'War_dataset.csv', encoding='utf-8')

        self.all_countries = set(self.inflation_df['Country'].unique())
        self.all_regions = set(self.continental_df['Country'].unique())

    def find_closest_match(self, query: str, choices: set) -> str | None:
        """Find the closest matching country/region."""
        matches = get_close_matches(query.lower(), [c.lower() for c in choices], n=1, cutoff=0.6)
        if matches:
            for choice in choices:
                if choice.lower() == matches[0]:
                    return choice
        return None

    def answer_question(self, question: str) -> tuple[str, object]:
        """Process a question and return (answer_text, visualization_figure)."""
        q_lower = question.lower()

        if 'highest inflation' in q_lower or 'max inflation' in q_lower:
            return self._highest_inflation(question)
        elif 'lowest inflation' in q_lower or 'min inflation' in q_lower:
            return self._lowest_inflation(question)
        elif 'compare' in q_lower or 'vs' in q_lower or 'versus' in q_lower:
            return self._compare_countries(question)
        elif 'trend' in q_lower or 'over time' in q_lower or 'history' in q_lower:
            return self._inflation_trend(question)
        elif 'region' in q_lower or 'continent' in q_lower or 'africa' in q_lower or 'asia' in q_lower or 'europe' in q_lower:
            return self._regional_inflation(question)
        elif 'average' in q_lower or 'mean' in q_lower or 'typical' in q_lower:
            return self._average_inflation(question)
        elif any(str(year) in q_lower for year in range(2020, 2027)):
            return self._inflation_by_year(question)
        else:
            return self._help_message(), None

    def _highest_inflation(self, question: str) -> tuple[str, object]:
        """Find highest inflation for a country."""
        for country in self.all_countries:
            if country.lower() in question.lower():
                country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
                if not country_data.empty:
                    max_row = country_data.loc[country_data['Inflation_rate'].idxmax()]
                    answer = (f"Highest inflation in {country}: {max_row['Inflation_rate']:.2f}% "
                            f"in {int(max_row['Year'])}")
                    fig = px.line(country_data, x='Year', y='Inflation_rate', 
                                 title=f"{country} - Inflation Over Time",
                                 markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                    fig.update_layout(template='plotly_white', height=400)
                    return answer, fig

        match = self.find_closest_match(question.split()[-1], self.all_countries)
        if match:
            country_data = self.inflation_df[self.inflation_df['Country'] == match].sort_values('Year')
            max_row = country_data.loc[country_data['Inflation_rate'].idxmax()]
            answer = (f"Highest inflation in {match}: {max_row['Inflation_rate']:.2f}% "
                    f"in {int(max_row['Year'])}")
            fig = px.line(country_data, x='Year', y='Inflation_rate', 
                         title=f"{match} - Inflation Over Time",
                         markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
            fig.update_layout(template='plotly_white', height=400)
            return answer, fig

        return "Please specify a country name.", None

    def _lowest_inflation(self, question: str) -> tuple[str, object]:
        """Find lowest inflation for a country."""
        for country in self.all_countries:
            if country.lower() in question.lower():
                country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
                if not country_data.empty:
                    min_row = country_data.loc[country_data['Inflation_rate'].idxmin()]
                    answer = (f"Lowest inflation in {country}: {min_row['Inflation_rate']:.2f}% "
                            f"in {int(min_row['Year'])}")
                    fig = px.line(country_data, x='Year', y='Inflation_rate', 
                                 title=f"{country} - Inflation Over Time",
                                 markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                    fig.update_layout(template='plotly_white', height=400)
                    return answer, fig

        match = self.find_closest_match(question.split()[-1], self.all_countries)
        if match:
            country_data = self.inflation_df[self.inflation_df['Country'] == match].sort_values('Year')
            min_row = country_data.loc[country_data['Inflation_rate'].idxmin()]
            answer = (f"Lowest inflation in {match}: {min_row['Inflation_rate']:.2f}% "
                    f"in {int(min_row['Year'])}")
            fig = px.line(country_data, x='Year', y='Inflation_rate', 
                         title=f"{match} - Inflation Over Time",
                         markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
            fig.update_layout(template='plotly_white', height=400)
            return answer, fig

        return "Please specify a country name.", None

    def _compare_countries(self, question: str) -> tuple[str, object]:
        """Compare inflation between two countries."""
        countries_in_q = [c for c in self.all_countries if c.lower() in question.lower()]

        if len(countries_in_q) >= 2:
            c1, c2 = countries_in_q[0], countries_in_q[1]
            d1_data = self.inflation_df[self.inflation_df['Country'] == c1].sort_values('Year')
            d2_data = self.inflation_df[self.inflation_df['Country'] == c2].sort_values('Year')
            
            d1_avg = d1_data['Inflation_rate'].mean()
            d2_avg = d2_data['Inflation_rate'].mean()
            diff = abs(d1_avg - d2_avg)
            higher = c1 if d1_avg > d2_avg else c2
            
            answer = (f"Average inflation: {c1} = {d1_avg:.2f}%, {c2} = {d2_avg:.2f}%. "
                    f"{higher} has higher inflation by {diff:.2f} percentage points.")
            
            combined = pd.concat([
                d1_data[['Year', 'Inflation_rate']].assign(Country=c1),
                d2_data[['Year', 'Inflation_rate']].assign(Country=c2)
            ])
            fig = px.line(combined, x='Year', y='Inflation_rate', color='Country', markers=True,
                         title=f"Inflation Comparison: {c1} vs {c2}",
                         labels={'Inflation_rate': 'Inflation Rate (%)'})
            fig.update_layout(template='plotly_white', height=400)
            return answer, fig

        return "Please mention two country names to compare.", None

    def _inflation_trend(self, question: str) -> tuple[str, object]:
        """Show inflation trend for a country."""
        for country in self.all_countries:
            if country.lower() in question.lower():
                country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
                if not country_data.empty:
                    first_yr = country_data.iloc[0]
                    last_yr = country_data.iloc[-1]
                    change = last_yr['Inflation_rate'] - first_yr['Inflation_rate']
                    trend = "increased" if change > 0 else "decreased"
                    answer = (f"{country} inflation {trend} from {first_yr['Inflation_rate']:.2f}% ({int(first_yr['Year'])}) "
                            f"to {last_yr['Inflation_rate']:.2f}% ({int(last_yr['Year'])}), a change of {change:.2f}%.")
                    
                    fig = px.line(country_data, x='Year', y='Inflation_rate', 
                                 title=f"{country} - Inflation Trend",
                                 markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                    fig.update_layout(template='plotly_white', height=400)
                    return answer, fig

        return "Please specify a country name.", None

    def _regional_inflation(self, question: str) -> tuple[str, object]:
        """Show regional inflation data."""
        for region in self.all_regions:
            if region.lower() in question.lower():
                region_data = self.continental_df[self.continental_df['Country'] == region].sort_values('Year')
                if not region_data.empty:
                    latest = region_data.iloc[-1]
                    avg = region_data['Inflation_rate'].mean()
                    answer = (f"{region}: Current inflation (2026) = {latest['Inflation_rate']:.2f}%, "
                            f"Average = {avg:.2f}%")
                    
                    fig = px.line(region_data, x='Year', y='Inflation_rate', 
                                 title=f"{region} - Inflation Over Time",
                                 markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                    fig.update_layout(template='plotly_white', height=400)
                    return answer, fig

        all_regions_data = self.continental_df.sort_values('Year')
        latest_year = all_regions_data[all_regions_data['Year'] == all_regions_data['Year'].max()]
        fig = px.bar(latest_year.sort_values('Inflation_rate', ascending=False), 
                    x='Country', y='Inflation_rate',
                    title="Regional Inflation (2026)",
                    labels={'Inflation_rate': 'Inflation Rate (%)', 'Country': 'Region'})
        fig.update_layout(template='plotly_white', height=400)
        return "Here are all regional inflation rates for 2026.", fig

    def _average_inflation(self, question: str) -> tuple[str, object]:
        """Calculate average inflation with visualization."""
        for country in self.all_countries:
            if country.lower() in question.lower():
                country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
                avg = country_data['Inflation_rate'].mean()
                answer = f"Average inflation for {country}: {avg:.2f}%"
                
                fig = px.line(country_data, x='Year', y='Inflation_rate', 
                             title=f"{country} - Inflation with Average Line",
                             markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                fig.add_hline(y=avg, line_dash="dash", line_color="red", 
                             annotation_text=f"Average: {avg:.2f}%")
                fig.update_layout(template='plotly_white', height=400)
                return answer, fig

        global_avg = self.inflation_df['Inflation_rate'].mean()
        answer = f"Global average inflation (all countries): {global_avg:.2f}%"
        return answer, None

    def _inflation_by_year(self, question: str) -> tuple[str, object]:
        """Find inflation for a specific year with visualization."""
        for year in range(2020, 2027):
            if str(year) in question:
                for country in self.all_countries:
                    if country.lower() in question.lower():
                        data = self.inflation_df[(self.inflation_df['Country'] == country) & 
                                                (self.inflation_df['Year'] == year)]
                        if not data.empty:
                            rate = data.iloc[0]['Inflation_rate']
                            answer = f"{country} inflation in {year}: {rate:.2f}%"
                            
                            country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
                            fig = px.line(country_data, x='Year', y='Inflation_rate', 
                                         title=f"{country} - Inflation Over Time",
                                         markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                            fig.add_vline(x=year, line_dash="dash", line_color="green",
                                         annotation_text=f"{year}: {rate:.2f}%")
                            fig.update_layout(template='plotly_white', height=400)
                            return answer, fig
                break

        return "Please specify both a year and a country.", None

    def _help_message(self) -> str:
        """Return help message with example questions."""
        return (
            "I can help answer questions about inflation data! Try asking:\n\n"
            "📊 **Examples:**\n"
            "- 'What was the highest inflation in Nigeria?'\n"
            "- 'Compare inflation in USA vs UK'\n"
            "- 'What is the inflation trend in India?'\n"
            "- 'What is the average inflation in Europe?'\n"
            "- 'What was the inflation in Germany in 2022?'\n"
            "- 'Lowest inflation in Canada?'\n\n"
            "Feel free to ask any question about inflation rates!"
        )
