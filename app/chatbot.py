import pandas as pd
from pathlib import Path
from difflib import get_close_matches
import plotly.express as px
import re

from app.utils import calculate_summary_stats, get_top_bottom_countries

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
        self.greeting_keywords = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        self.farewell_keywords = ['bye', 'goodbye', 'see you', 'talk later', 'see ya']
        self.thanks_keywords = ['thank', 'thanks', 'thank you', 'appreciate']
        self.country_aliases = {
            'usa': 'United States',
            'u s a': 'United States',
            'us': 'United States',
            'u s': 'United States',
            'u.s.a': 'United States',
            'u.s.': 'United States',
            'america': 'United States',
            'united states of america': 'United States',
            'uk': 'United Kingdom',
            'u k': 'United Kingdom',
            'u.k.': 'United Kingdom',
            'britain': 'United Kingdom',
            'great britain': 'United Kingdom',
            'england': 'United Kingdom',
            'china': "China, People's Republic of",
            'pr china': "China, People's Republic of",
            'people s republic of china': "China, People's Republic of",
            'south korea': 'Korea, Rep.',
            'north korea': 'Korea, Dem. People\'s Rep.',
            'russia': 'Russian Federation',
            'uae': 'United Arab Emirates',
            'ivory coast': 'Côte d\'Ivoire'
        }

    def _normalize(self, text: str) -> str:
        # make sure 'vs' stuck to words becomes separated (e.g. 'vsUK' -> 'vs UK')
        t = text.lower()
        t = re.sub(r'(?<=\w)vs(?=\w)', ' vs ', t)
        # replace any non-alphanumeric (except space) with space
        t = re.sub(r'[^a-z0-9 ]', ' ', t)
        return re.sub(r'\s+', ' ', t).strip()

    def _contains_keyword(self, text: str, keywords: list[str]) -> bool:
        normalized = f" {self._normalize(text)} "
        return any(f" {keyword} " in normalized for keyword in keywords)

    def find_closest_match(self, query: str, choices: set) -> str | None:
        """Find the closest matching country/region."""
        matches = get_close_matches(query.lower(), [c.lower() for c in choices], n=1, cutoff=0.6)
        if matches:
            for choice in choices:
                if choice.lower() == matches[0]:
                    return choice
        return None

    def _extract_countries(self, question: str, limit: int = 3) -> list[str]:
        normalized = self._normalize(question)
        tokens = normalized.split()
        found = []

        # First pass: exact alias phrase matching.
        padded = f" {normalized} "
        for alias, name in self.country_aliases.items():
            alias_norm = self._normalize(alias)
            if f" {alias_norm} " in padded and name not in found:
                found.append(name)
                if len(found) >= limit:
                    return found[:limit]

        # Second pass: exact country name phrase matching.
        for country in self.all_countries:
            country_norm = self._normalize(country)
            if f" {country_norm} " in padded and country not in found:
                found.append(country)
                if len(found) >= limit:
                    return found[:limit]

        # Third pass: token-level fuzzy matching, only if we still found nothing.
        if found:
            return found[:limit]

        for token in tokens:
            if len(token) <= 2:
                continue
            match = self.find_closest_match(token, self.all_countries)
            if match and match not in found:
                found.append(match)
            alias_match = self.find_closest_match(token, set(self.country_aliases.keys()))
            if alias_match and alias_match in self.country_aliases:
                country_name = self.country_aliases[alias_match]
                if country_name not in found:
                    found.append(country_name)
            if len(found) >= limit:
                break

        return found[:limit]

    def _extract_years(self, question: str) -> list[int]:
        return [int(match) for match in re.findall(r'\b(?:19|20)\d{2}\b', question)]

    def _extract_chart_type(self, question: str) -> str | None:
        normalized = question.lower()
        if 'pie' in normalized:
            return 'pie'
        if 'bar' in normalized or 'column' in normalized:
            return 'bar'
        if 'line' in normalized or 'trend' in normalized:
            return 'line'
        return None

    def _extract_regions(self, question: str) -> list[str]:
        normalized = self._normalize(question)
        return [region for region in self.all_regions if region.lower() in normalized]

    def _get_dataset(self, question: str):
        q_lower = question.lower()
        if 'covid' in q_lower or 'pandemic' in q_lower:
            return self.covid_df, 'COVID-19'
        if 'war' in q_lower or 'conflict' in q_lower or 'battle' in q_lower:
            return self.war_df, 'War'
        if 'region' in q_lower or 'continent' in q_lower or 'regional' in q_lower or 'country wise' in q_lower or 'africa' in q_lower or 'asia' in q_lower or 'europe' in q_lower:
            return self.continental_df, 'Regional'
        return self.inflation_df, 'Global'

    def answer_question(self, question: str) -> tuple[str, object]:
        """Process a question and return (answer_text, visualization_figure)."""
        q_lower = question.lower()

        if self._contains_keyword(question, self.greeting_keywords):
            return self._greet()
        if self._contains_keyword(question, self.farewell_keywords):
            return self._farewell()
        if self._contains_keyword(question, self.thanks_keywords):
            return self._thank_you()
        if 'who are you' in q_lower or 'what are you' in q_lower:
            return self._introduce()
        if 'what is inflation' in q_lower or 'define inflation' in q_lower or 'inflation means' in q_lower:
            return self._explain_inflation()

        if 'compare' in q_lower or ' vs ' in q_lower or ' versus ' in q_lower:
            return self._compare_countries(question)
        if 'trend' in q_lower or 'over time' in q_lower or 'history' in q_lower:
            return self._inflation_trend(question)
        if 'covid' in q_lower or 'pandemic' in q_lower:
            return self._covid_insight(question)
        if 'war' in q_lower or 'conflict' in q_lower:
            return self._war_insight(question)
        if 'most volatile' in q_lower or 'volatility' in q_lower or 'stable inflation' in q_lower:
            return self._volatility(question)
        if 'top countries' in q_lower or 'highest countries' in q_lower or ('top' in q_lower and 'inflation' in q_lower):
            return self._top_inflation_countries(question)
        if 'lowest countries' in q_lower or 'least inflation' in q_lower or ('lowest' in q_lower and 'inflation' in q_lower and 'country' in q_lower):
            return self._bottom_inflation_countries(question)
        if 'what happened' in q_lower or 'year summary' in q_lower or 'in ' in q_lower and any(str(year) in q_lower for year in range(2020, 2027)):
            return self._year_summary(question)
        if 'highest inflation' in q_lower or 'max inflation' in q_lower:
            return self._highest_inflation(question)
        if 'lowest inflation' in q_lower or 'min inflation' in q_lower:
            return self._lowest_inflation(question)
        if 'average' in q_lower or 'mean' in q_lower or 'typical' in q_lower:
            return self._average_inflation(question)
        if any(str(year) in q_lower for year in range(2020, 2027)):
            return self._inflation_by_year(question)
        if 'region' in q_lower or 'continent' in q_lower:
            return self._regional_inflation(question)

        return self._help_message(), None

    def build_support_data(self, question: str) -> dict | None:
        dataset, label = self._get_dataset(question)
        years = self._extract_years(question)
        countries = self._extract_countries(question, limit=10)

        if label == 'Regional':
            regions = self._extract_regions(question)
            if regions:
                countries = regions

        filtered = dataset.copy()
        if countries:
            filtered = filtered[filtered['Country'].isin(countries)]
        if years:
            if len(years) == 1:
                filtered = filtered[filtered['Year'] == years[0]]
            else:
                filtered = filtered[filtered['Year'].between(years[0], years[-1])]

        if filtered.empty:
            return None

        summary_stats = calculate_summary_stats(filtered)
        highest, lowest = get_top_bottom_countries(filtered)
        return {
            "dataset_label": label,
            "filtered_df": filtered,
            "summary_stats": summary_stats,
            "highest": highest,
            "lowest": lowest,
        }

    def _greet(self) -> tuple[str, object]:
        return "Hello! I am your inflation data assistant. Ask me about countries, regions, COVID trends or war-related inflation.", None

    def _farewell(self) -> tuple[str, object]:
        return "It was great helping you. Come back anytime if you want another inflation insight!", None

    def _thank_you(self) -> tuple[str, object]:
        return "You're welcome! I'm always ready to answer another question.", None

    def _introduce(self) -> tuple[str, object]:
        return ("I am an advanced inflation analysis assistant built for your dashboard. "
                "Ask me about trends, country comparisons, pandemic-era inflation, regional patterns, and more."), None

    def _explain_inflation(self) -> tuple[str, object]:
        return ("Inflation is the rate at which the average price level of goods and services rises over time. "
                "When inflation is high, each unit of currency buys less than before; when it is low, prices are more stable."), None

    def _top_inflation_countries(self, question: str) -> tuple[str, object]:
        years = self._extract_years(question)
        year = years[0] if years else int(self.inflation_df['Year'].max())
        dataset, label = self._get_dataset(question)
        year_data = dataset[dataset['Year'] == year]

        if year_data.empty:
            return f"I couldn't find data for {year}. Try another year between 1980 and 2026.", None

        top5 = year_data.nlargest(5, 'Inflation_rate')
        names = ', '.join([f"{row['Country']} ({row['Inflation_rate']:.1f}%)" for _, row in top5.iterrows()])
        answer = f"In {year}, the highest inflation countries were: {names}." \
                 f" Here's the top 5 for {label} data."
        fig = px.bar(top5, x='Country', y='Inflation_rate', title=f"Top 5 Inflation Countries in {year}",
                     labels={'Inflation_rate': 'Inflation Rate (%)', 'Country': 'Country'})
        fig.update_layout(template='plotly_white', height=420)
        return answer, fig

    def _bottom_inflation_countries(self, question: str) -> tuple[str, object]:
        years = self._extract_years(question)
        year = years[0] if years else int(self.inflation_df['Year'].max())
        dataset, label = self._get_dataset(question)
        year_data = dataset[dataset['Year'] == year]

        if year_data.empty:
            return f"I couldn't find data for {year}. Try another year between 1980 and 2026.", None

        bottom5 = year_data.nsmallest(5, 'Inflation_rate')
        names = ', '.join([f"{row['Country']} ({row['Inflation_rate']:.1f}%)" for _, row in bottom5.iterrows()])
        answer = f"In {year}, the lowest inflation countries were: {names}." \
                 f" Here's a quick look at the calmest inflation markets."
        fig = px.bar(bottom5.sort_values('Inflation_rate'), x='Country', y='Inflation_rate',
                     title=f"Lowest Inflation Countries in {year}",
                     labels={'Inflation_rate': 'Inflation Rate (%)', 'Country': 'Country'})
        fig.update_layout(template='plotly_white', height=420)
        return answer, fig

    def _year_summary(self, question: str) -> tuple[str, object]:
        years = self._extract_years(question)
        if not years:
            return self._help_message(), None

        year = years[0]
        dataset, label = self._get_dataset(question)
        year_data = dataset[dataset['Year'] == year]
        if year_data.empty:
            return f"There is no data for {year} in this dataset.", None

        top = year_data.nlargest(3, 'Inflation_rate')
        bottom = year_data.nsmallest(3, 'Inflation_rate')
        top_names = ', '.join([f"{r['Country']} ({r['Inflation_rate']:.1f}%)" for _, r in top.iterrows()])
        bottom_names = ', '.join([f"{r['Country']} ({r['Inflation_rate']:.1f}%)" for _, r in bottom.iterrows()])
        answer = (f"In {year}, the strongest inflation pressures in {label} data were {top_names}. "
                  f"The calmest inflation rates were {bottom_names}.")

        combined = pd.concat([top, bottom], ignore_index=True)
        fig = px.bar(combined.sort_values('Inflation_rate', ascending=False),
                     x='Country', y='Inflation_rate', color='Inflation_rate',
                     title=f"Top and Bottom Inflation in {year}",
                     labels={'Inflation_rate': 'Inflation Rate (%)'})
        fig.update_layout(template='plotly_white', height=420, showlegend=False)
        return answer, fig

    def _covid_insight(self, question: str) -> tuple[str, object]:
        countries = self._extract_countries(question)
        if countries:
            country = countries[0]
            data = self.covid_df[self.covid_df['Country'] == country].sort_values('Year')
            if data.empty:
                return f"I could not find COVID-era data for {country}.", None
            answer = (f"During the COVID era, {country} saw inflation ranging from {data['Inflation_rate'].min():.1f}% "
                      f"to {data['Inflation_rate'].max():.1f}% across available years.")
            fig = px.line(data, x='Year', y='Inflation_rate', markers=True,
                         title=f"COVID-era Inflation in {country}",
                         labels={'Inflation_rate': 'Inflation Rate (%)'})
            fig.update_layout(template='plotly_white', height=420)
            return answer, fig

        current = self.covid_df[self.covid_df['Year'] == self.covid_df['Year'].max()]
        top5 = current.nlargest(5, 'Inflation_rate')
        answer = ("Here are the top 5 countries with the highest COVID-era inflation for the latest reported year. "
                  "This helps identify the most affected economies.")
        fig = px.bar(top5, x='Country', y='Inflation_rate',
                     title=f"Highest COVID-era Inflation ({int(current['Year'].max())})",
                     labels={'Inflation_rate': 'Inflation Rate (%)'})
        fig.update_layout(template='plotly_white', height=420)
        return answer, fig

    def _war_insight(self, question: str) -> tuple[str, object]:
        countries = self._extract_countries(question)
        if countries:
            country = countries[0]
            data = self.war_df[self.war_df['Country'] == country].sort_values('Year')
            if data.empty:
                return f"I don't have war-era data for {country}.", None
            answer = (f"In conflict-affected years, {country} had inflation from {data['Inflation_rate'].min():.1f}% "
                      f"to {data['Inflation_rate'].max():.1f}%.")
            fig = px.line(data, x='Year', y='Inflation_rate', markers=True,
                         title=f"War-era Inflation in {country}",
                         labels={'Inflation_rate': 'Inflation Rate (%)'})
            fig.update_layout(template='plotly_white', height=420)
            return answer, fig

        summary = self.war_df.groupby('Country')['Inflation_rate'].mean().reset_index().nlargest(5, 'Inflation_rate')
        answer = "These countries had the highest average inflation in our war dataset."
        fig = px.bar(summary, x='Country', y='Inflation_rate',
                     title="Top War-era Inflation Countries",
                     labels={'Inflation_rate': 'Average Inflation Rate (%)'})
        fig.update_layout(template='plotly_white', height=420)
        return answer, fig

    def _volatility(self, question: str) -> tuple[str, object]:
        dataset, label = self._get_dataset(question)
        volatility = dataset.groupby('Country')['Inflation_rate'].std().reset_index().dropna().nlargest(5, 'Inflation_rate')
        answer = (f"These countries show the most variable inflation patterns in {label} data. "
                  "Volatility can signal shifting economic pressure.")
        fig = px.bar(volatility, x='Country', y='Inflation_rate',
                     title=f"Most Volatile Inflation in {label} Data",
                     labels={'Inflation_rate': 'Inflation Rate Std Dev (%)'})
        fig.update_layout(template='plotly_white', height=420)
        return answer, fig

    def _highest_inflation(self, question: str) -> tuple[str, object]:
        """Find highest inflation for a country."""
        countries = self._extract_countries(question)
        if countries:
            country = countries[0]
            country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
            if not country_data.empty:
                max_row = country_data.loc[country_data['Inflation_rate'].idxmax()]
                answer = (f"I found that {country}'s highest inflation was {max_row['Inflation_rate']:.2f}% "
                          f"in {int(max_row['Year'])}.")
                fig = px.line(country_data, x='Year', y='Inflation_rate',
                             title=f"{country} - Inflation Over Time",
                             markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                fig.update_layout(template='plotly_white', height=420)
                return answer, fig

        return "I couldn't identify the country. Please tell me which country you mean.", None

    def _lowest_inflation(self, question: str) -> tuple[str, object]:
        """Find lowest inflation for a country."""
        countries = self._extract_countries(question)
        if countries:
            country = countries[0]
            country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
            if not country_data.empty:
                min_row = country_data.loc[country_data['Inflation_rate'].idxmin()]
                answer = (f"I found that {country}'s lowest reported inflation was {min_row['Inflation_rate']:.2f}% "
                          f"in {int(min_row['Year'])}.")
                fig = px.line(country_data, x='Year', y='Inflation_rate',
                             title=f"{country} - Inflation Over Time",
                             markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                fig.update_layout(template='plotly_white', height=420)
                return answer, fig

        return "I couldn't identify the country. Please share the country name.", None

    def _compare_countries(self, question: str) -> tuple[str, object]:
        """Compare inflation between two countries."""
        countries = self._extract_countries(question, limit=2)
        if len(countries) >= 2:
            c1, c2 = countries[0], countries[1]
            # Get the appropriate dataset based on question content
            dataset, label = self._get_dataset(question)
            
            # Handle dataset-country mismatch early
            missing_countries = [c for c in (c1, c2) if c not in dataset['Country'].values]
            if missing_countries:
                missing_text = " and ".join(missing_countries)
                return (f"I don't have {missing_text} in the selected {label} dataset. "
                        "Try Global, COVID-era, or War-era with countries that exist there."), None
            
            # Extract years if specified
            years = self._extract_years(question)
            
            # Filter data for both countries
            d1_data = dataset[dataset['Country'] == c1].sort_values('Year')
            d2_data = dataset[dataset['Country'] == c2].sort_values('Year')
            
            # Apply year filter if specified
            if years:
                if len(years) == 1:
                    d1_data = d1_data[d1_data['Year'] == years[0]]
                    d2_data = d2_data[d2_data['Year'] == years[0]]
                else:
                    d1_data = d1_data[(d1_data['Year'] >= years[0]) & (d1_data['Year'] <= years[-1])]
                    d2_data = d2_data[(d2_data['Year'] >= years[0]) & (d2_data['Year'] <= years[-1])]
            
            if d1_data.empty or d2_data.empty:
                return f"No data available for {c1} or {c2} in the selected parameters.", None
            
            d1_avg = d1_data['Inflation_rate'].mean()
            d2_avg = d2_data['Inflation_rate'].mean()
            higher = c1 if d1_avg > d2_avg else c2
            year_range = f" ({years[0]}-{years[-1]})" if years else ""
            answer = (f"Comparing {c1} and {c2}{year_range} in {label} data: {higher} has higher average inflation. "
                      f"{c1} averaged {d1_avg:.2f}% and {c2} averaged {d2_avg:.2f}%.")
            chart_type = self._extract_chart_type(question) or 'line'
            combined = pd.concat([
                d1_data[['Year', 'Inflation_rate']].assign(Country=c1),
                d2_data[['Year', 'Inflation_rate']].assign(Country=c2)
            ])

            if chart_type == 'bar':
                fig = px.bar(combined, x='Year', y='Inflation_rate', color='Country', barmode='group',
                             title=f"Inflation Comparison: {c1} vs {c2}{year_range}",
                             labels={'Inflation_rate': 'Inflation Rate (%)'})
            elif chart_type == 'pie':
                pie_data = pd.DataFrame({
                    'Country': [c1, c2],
                    'Inflation_rate': [d1_avg, d2_avg]
                })
                fig = px.pie(pie_data, values='Inflation_rate', names='Country',
                             title=f"Average Inflation Comparison: {c1} vs {c2}{year_range}")
            else:
                fig = px.line(combined, x='Year', y='Inflation_rate', color='Country', markers=True,
                             title=f"Inflation Comparison: {c1} vs {c2}{year_range}",
                             labels={'Inflation_rate': 'Inflation Rate (%)'})

            fig.update_layout(template='plotly_white', height=420)
            return answer, fig

        return "I need two country names to compare. Please mention them both.", None

    def _inflation_trend(self, question: str) -> tuple[str, object]:
        """Show inflation trend for a country."""
        countries = self._extract_countries(question)
        if countries:
            country = countries[0]
            country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
            if not country_data.empty:
                first_yr = country_data.iloc[0]
                last_yr = country_data.iloc[-1]
                change = last_yr['Inflation_rate'] - first_yr['Inflation_rate']
                trend = "increased" if change > 0 else "decreased"
                answer = (f"{country}'s inflation has {trend} from {first_yr['Inflation_rate']:.2f}% "
                          f"in {int(first_yr['Year'])} to {last_yr['Inflation_rate']:.2f}% in {int(last_yr['Year'])}. "
                          f"That's a {abs(change):.2f}% change.")
                fig = px.line(country_data, x='Year', y='Inflation_rate',
                             title=f"{country} - Inflation Trend",
                             markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                fig.update_layout(template='plotly_white', height=420)
                return answer, fig

        return "I couldn't identify the country when checking the trend. Please include the country name.", None

    def _regional_inflation(self, question: str) -> tuple[str, object]:
        """Show regional inflation data."""
        regions = self._extract_regions(question)
        if regions:
            region = regions[0]
            region_data = self.continental_df[self.continental_df['Country'] == region].sort_values('Year')
            if not region_data.empty:
                latest = region_data.iloc[-1]
                avg = region_data['Inflation_rate'].mean()
                answer = (f"{region}'s latest inflation is {latest['Inflation_rate']:.2f}% in {int(latest['Year'])}. "
                          f"The average regional inflation is {avg:.2f}%.")
                fig = px.line(region_data, x='Year', y='Inflation_rate',
                             title=f"{region} - Inflation Over Time",
                             markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                fig.update_layout(template='plotly_white', height=420)
                return answer, fig

        all_regions_data = self.continental_df.sort_values('Year')
        latest_year = all_regions_data[all_regions_data['Year'] == all_regions_data['Year'].max()]
        fig = px.bar(latest_year.sort_values('Inflation_rate', ascending=False),
                    x='Country', y='Inflation_rate',
                    title="Regional Inflation (Latest Year)",
                    labels={'Inflation_rate': 'Inflation Rate (%)', 'Country': 'Region'})
        fig.update_layout(template='plotly_white', height=420)
        return "Here are the latest regional inflation rates.", fig

    def _average_inflation(self, question: str) -> tuple[str, object]:
        """Calculate average inflation with visualization."""
        countries = self._extract_countries(question)
        if countries:
            country = countries[0]
            country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
            avg = country_data['Inflation_rate'].mean()
            answer = f"Average inflation for {country}: {avg:.2f}%"
            fig = px.line(country_data, x='Year', y='Inflation_rate',
                         title=f"{country} - Inflation with Average Line",
                         markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
            fig.add_hline(y=avg, line_dash='dash', line_color='red',
                         annotation_text=f"Average: {avg:.2f}%")
            fig.update_layout(template='plotly_white', height=420)
            return answer, fig

        global_avg = self.inflation_df['Inflation_rate'].mean()
        answer = f"Global average inflation across all countries is {global_avg:.2f}%"
        return answer, None

    def _inflation_by_year(self, question: str) -> tuple[str, object]:
        """Find inflation for a specific year with visualization."""
        years = self._extract_years(question)
        if not years:
            return "Please specify a year and optionally a country.", None

        year = years[0]
        countries = self._extract_countries(question)
        if countries:
            country = countries[0]
            data = self.inflation_df[(self.inflation_df['Country'] == country) &
                                    (self.inflation_df['Year'] == year)]
            if not data.empty:
                rate = data.iloc[0]['Inflation_rate']
                answer = f"{country} had inflation of {rate:.2f}% in {year}."
                country_data = self.inflation_df[self.inflation_df['Country'] == country].sort_values('Year')
                fig = px.line(country_data, x='Year', y='Inflation_rate',
                             title=f"{country} - Inflation Over Time",
                             markers=True, labels={'Inflation_rate': 'Inflation Rate (%)'})
                fig.add_vline(x=year, line_dash='dash', line_color='green',
                             annotation_text=f"{year}: {rate:.2f}%")
                fig.update_layout(template='plotly_white', height=420)
                return answer, fig

        year_data = self.inflation_df[self.inflation_df['Year'] == year]
        if year_data.empty:
            return f"I couldn't find data for {year}.", None

        top3 = year_data.nlargest(3, 'Inflation_rate')
        names = ', '.join([f"{row['Country']} ({row['Inflation_rate']:.1f}%)" for _, row in top3.iterrows()])
        answer = f"In {year}, the top inflation countries were {names}."
        fig = px.bar(top3, x='Country', y='Inflation_rate',
                     title=f"Top Inflation Countries in {year}",
                     labels={'Inflation_rate': 'Inflation Rate (%)'})
        fig.update_layout(template='plotly_white', height=420)
        return answer, fig

    def _help_message(self) -> str:
        return (
            "I can help answer questions about inflation data.\n\n"
            "Try asking:\n"
            "- What was the highest inflation in Nigeria?\n"
            "- Compare inflation in USA vs UK\n"
            "- What is the inflation trend in India?\n"
            "- What was inflation in Germany in 2022?\n"
            "- Show me top countries by inflation in 2026\n"
            "- What happened during the COVID pandemic?\n"
            "- Which regions are most stable?"
        )

