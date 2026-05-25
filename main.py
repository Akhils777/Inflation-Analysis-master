import streamlit as st

from app.app import run
from app.app1 import run1
from app.app2 import run2
from app.app3 import run3
from app.chatbot import InflationChatbot


def _init_chat_state() -> None:
    st.session_state.setdefault("view_mode", "Home")
    st.session_state.setdefault("last_manual_view", "Home")
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("chat_pending", None)
    st.session_state.setdefault("chat_partial", {})
    st.session_state.setdefault("chat_last_fig", None)
    st.session_state.setdefault("chat_last_support", None)


def _reset_chat_state() -> None:
    st.session_state["chat_history"] = []
    st.session_state["chat_pending"] = None
    st.session_state["chat_partial"] = {}
    st.session_state["chat_last_fig"] = None
    st.session_state["chat_last_support"] = None


def _is_compare_query(chatbot: InflationChatbot, text: str) -> bool:
    normalized = f" {chatbot._normalize(text)} "
    return " compare " in normalized or " versus " in normalized or " vs " in normalized


def _dataset_options() -> dict[str, str]:
    return {
        "global": "Global",
        "covid": "COVID-era",
        "war": "War-era",
        "region": "Region Wise",
    }


def _chart_options() -> dict[str, str]:
    return {
        "line": "Line",
        "bar": "Bar",
        "pie": "Pie",
    }


def _extract_chart_type(chatbot: InflationChatbot, text: str) -> str | None:
    helper = getattr(chatbot, "_extract_chart_type", None)
    if callable(helper):
        return helper(text)

    normalized = text.lower()
    if "pie" in normalized:
        return "pie"
    if "bar" in normalized or "column" in normalized:
        return "bar"
    if "line" in normalized or "trend" in normalized:
        return "line"
    return None


def _set_bot_reply(message: str, fig=None, support_data=None) -> None:
    st.session_state.chat_history.append(("bot", message))
    st.session_state.chat_last_fig = fig
    st.session_state.chat_last_support = support_data


def _finalize_answer(chatbot: InflationChatbot) -> None:
    partial = st.session_state.chat_partial
    original = partial.get("original", "")
    dataset = partial.get("dataset", "")
    years = partial.get("years_text", "")
    chart_type = partial.get("chart_type", "")
    countries = partial.get("countries_text", "")

    combined = " ".join(filter(None, [original, countries, dataset, years, chart_type]))
    answer, fig = chatbot.answer_question(combined)
    support_data = chatbot.build_support_data(combined)
    _set_bot_reply(answer, fig, support_data)
    st.session_state.chat_pending = None
    st.session_state.chat_partial = {}


def _render_support_data() -> None:
    support_data = st.session_state.get("chat_last_support")
    if not support_data:
        return

    summary_stats = support_data.get("summary_stats")
    highest = support_data.get("highest")
    lowest = support_data.get("lowest")
    label = support_data.get("dataset_label", "Selected")

    if summary_stats is not None and not summary_stats.empty:
        st.subheader("Summary Statistics")
        st.table(summary_stats)
        csv_data = summary_stats.to_csv().encode("utf-8")
        st.download_button(
            label="Download Summary Stats as CSV",
            data=csv_data,
            file_name="chatbot_summary_stats.csv",
            mime="text/csv",
        )

    if highest is not None and not highest.empty:
        st.subheader(f"Highest Average Inflation in {label} Data")
        st.table(highest)

    if lowest is not None and not lowest.empty:
        st.subheader(f"Lowest Average Inflation in {label} Data")
        st.table(lowest)


def _start_compare_flow(chatbot: InflationChatbot, user_input: str) -> bool:
    countries = chatbot._extract_countries(user_input, limit=2)
    years = chatbot._extract_years(user_input)
    chart_type = _extract_chart_type(chatbot, user_input)
    normalized = chatbot._normalize(user_input)

    dataset_key = None
    if " covid " in f" {normalized} " or " pandemic " in f" {normalized} ":
        dataset_key = "covid"
    elif " war " in f" {normalized} " or " conflict " in f" {normalized} ":
        dataset_key = "war"
    elif " region " in f" {normalized} " or " continent " in f" {normalized} " or " regional " in f" {normalized} ":
        dataset_key = "region"
    elif " global " in f" {normalized} ":
        dataset_key = "global"

    st.session_state.chat_partial = {
        "original": user_input,
        "countries": countries,
        "countries_text": " ".join(countries),
        "dataset": dataset_key or "",
        "years": years,
        "years_text": "",
        "chart_type": chart_type or "",
    }

    if len(countries) < 2:
        st.session_state.chat_pending = "countries"
        _set_bot_reply("Which two countries would you like to compare?")
        return True

    if not dataset_key:
        st.session_state.chat_pending = "dataset"
        _set_bot_reply("Which condition should I use for the comparison: Global, COVID-era, War-era, or Region Wise?")
        return True

    if not years:
        st.session_state.chat_pending = "years"
        _set_bot_reply("Which year or year range should I use? For example: 2021 or 2020-2022.")
        return True

    st.session_state.chat_partial["years_text"] = f"{years[0]}" if len(years) == 1 else f"{years[0]}-{years[-1]}"

    if not chart_type:
        st.session_state.chat_pending = "chart_type"
        _set_bot_reply("Which chart type should I show: line, bar, or pie?")
        return True

    _finalize_answer(chatbot)
    return True


def _handle_pending_reply(chatbot: InflationChatbot, user_input: str) -> None:
    pending = st.session_state.chat_pending
    partial = st.session_state.chat_partial

    if pending == "countries":
        countries = chatbot._extract_countries(user_input, limit=2)
        if len(countries) < 2:
            _set_bot_reply("I still need two countries. Please enter both country names, like `India and Pakistan`.")
            return
        partial["countries"] = countries
        partial["countries_text"] = " ".join(countries)
        st.session_state.chat_pending = "dataset"
        _set_bot_reply("Which condition should I use for the comparison: Global, COVID-era, War-era, or Region Wise?")
        return

    if pending == "years":
        years = chatbot._extract_years(user_input)
        if not years:
            _set_bot_reply("I could not detect a year. Please enter a year or range like `2021` or `2020-2022`.")
            return
        partial["years"] = years
        partial["years_text"] = f"{years[0]}" if len(years) == 1 else f"{years[0]}-{years[-1]}"
        if not partial.get("chart_type"):
            st.session_state.chat_pending = "chart_type"
            _set_bot_reply("Which chart type should I show: line, bar, or pie?")
            return
        _finalize_answer(chatbot)
        return

    if pending == "chart_type":
        chart_type = _extract_chart_type(chatbot, user_input)
        if not chart_type:
            _set_bot_reply("Please enter one chart type: `line`, `bar`, or `pie`.")
            return
        partial["chart_type"] = chart_type
        _finalize_answer(chatbot)
        return

    if pending == "dataset":
        normalized = chatbot._normalize(user_input)
        dataset_key = None
        if " covid " in f" {normalized} ":
            dataset_key = "covid"
        elif " war " in f" {normalized} ":
            dataset_key = "war"
        elif " region " in f" {normalized} ":
            dataset_key = "region"
        elif " global " in f" {normalized} ":
            dataset_key = "global"

        if not dataset_key:
            _set_bot_reply("Please choose one condition: `global`, `covid`, `war`, or `region`.")
            return

        partial["dataset"] = dataset_key
        original = partial.get("original", "")
        countries = partial.get("countries", [])
        dataset_df, dataset_label = chatbot._get_dataset(dataset_key)
        missing = [country for country in countries if country not in set(dataset_df["Country"].unique())]
        if missing:
            names = " and ".join(missing)
            _set_bot_reply(f"{names} is not available in the {dataset_label} dataset. Please choose another condition.")
            return

        if not partial.get("years"):
            st.session_state.chat_pending = "years"
            _set_bot_reply("Which year or year range should I use? For example: 2021 or 2020-2022.")
            return

        if not partial.get("chart_type"):
            st.session_state.chat_pending = "chart_type"
            _set_bot_reply("Which chart type should I show: line, bar, or pie?")
            return

        _finalize_answer(chatbot)


def _render_chatbot() -> None:
    chatbot = InflationChatbot()
    _init_chat_state()

    st.title("Inflation Data Assistant")
    st.write("Ask in plain language. The chatbot will ask follow-up questions when your comparison is missing details.")

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Start New Conversation", use_container_width=True):
            _reset_chat_state()

    with st.expander("How it works", expanded=False):
        st.markdown(
            """
Ask things like:

- `Compare inflation in USA vs UK`
- `Compare inflation during covid in India and Pakistan from 2020 to 2022 as a bar chart`
- `What was the highest inflation in Nigeria?`
            """
        )

    for speaker, text in st.session_state.chat_history:
        label = "You" if speaker == "user" else "Bot"
        st.markdown(f"**{label}:** {text}")

    if st.session_state.chat_last_fig is not None:
        st.plotly_chart(st.session_state.chat_last_fig, use_container_width=True)
        _render_support_data()

    pending = st.session_state.chat_pending
    if pending == "dataset":
        st.markdown("**Choose condition:**")
        columns = st.columns(len(_dataset_options()))
        for (key, label), column in zip(_dataset_options().items(), columns):
            if column.button(label, key=f"dataset_{key}", use_container_width=True):
                st.session_state.chat_history.append(("user", label))
                _handle_pending_reply(chatbot, key)
                st.rerun()

    elif pending == "chart_type":
        st.markdown("**Choose chart type:**")
        columns = st.columns(len(_chart_options()))
        for (key, label), column in zip(_chart_options().items(), columns):
            if column.button(label, key=f"chart_{key}", use_container_width=True):
                st.session_state.chat_history.append(("user", label))
                _handle_pending_reply(chatbot, key)
                st.rerun()

    with st.form("chat_form", clear_on_submit=True):
        prompt = st.text_input(
            "Your question or reply",
            placeholder="Type your question and press Enter",
        )
        submitted = st.form_submit_button("Send")

    if submitted and prompt.strip():
        user_input = prompt.strip()
        st.session_state.chat_history.append(("user", user_input))

        if st.session_state.chat_pending:
            _handle_pending_reply(chatbot, user_input)
        elif _is_compare_query(chatbot, user_input):
            _start_compare_flow(chatbot, user_input)
        else:
            answer, fig = chatbot.answer_question(user_input)
            support_data = chatbot.build_support_data(user_input) if fig is not None else None
            _set_bot_reply(answer, fig, support_data)

        st.rerun()


def main() -> None:
    st.set_page_config(layout="wide")
    _init_chat_state()

    st.sidebar.markdown("### Navigation")
    selected_view = st.sidebar.selectbox(
        "Select Filter",
        ["Home", "Country Wise", "During COVID", "Region Wise", "During War"],
        key="view_mode_select",
    )

    if selected_view != st.session_state.get("last_manual_view"):
        st.session_state["last_manual_view"] = selected_view
        st.session_state["view_mode"] = selected_view

    if st.sidebar.button("Ask Chatbot", use_container_width=True):
        st.session_state["view_mode"] = "chatbot"

    current_view = st.session_state.get("view_mode", selected_view)
    if current_view != "chatbot":
        st.session_state["view_mode"] = selected_view
        current_view = selected_view

    if current_view == "Home":
        st.title("Inflation Rate Analysis")
        st.write(
            "This dashboard compares inflation trends across countries, COVID-era data, regional averages, and war-affected periods. "
            "Use the sidebar to choose the analysis mode and then select countries and dates."
        )
        st.image("world.png", caption="Global inflation overview")
    elif current_view == "Country Wise":
        run()
    elif current_view == "During COVID":
        run1()
    elif current_view == "Region Wise":
        run2()
    elif current_view == "During War":
        run3()
    else:
        _render_chatbot()


if __name__ == "__main__":
    main()
