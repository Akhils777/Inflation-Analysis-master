import streamlit as st
from app.app import run
from app.app1 import run1
from app.app2 import run2
from app.app3 import run3
from app.chatbot import InflationChatbot

def run_chatbot():
    st.title("Can I help you?")
    st.write("Ask me questions about inflation trends, comparisons, and statistics!")
    
    chatbot = InflationChatbot()
    
    with st.expander("How to use the chatbot", expanded=False):
        st.info(chatbot._help_message())
    
    user_question = st.text_input(
        "Your question:",
        placeholder="e.g., What was the highest inflation in Nigeria?",
        key="chatbot_input"
    )
    
    if user_question:
        response_text, figure = chatbot.answer_question(user_question)
        st.markdown("### Response")
        st.write(response_text)
        
        if figure is not None:
            st.plotly_chart(figure, use_container_width=True)
        
        st.divider()
        st.caption("Try asking about other countries, regions, or time periods!")

def main():
    st.set_page_config(layout="wide")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Navigation")
        app_selection = st.selectbox(
            "Select Filter",
            ["Home", "Country Wise", "During COVID", "Region Wise", "During War"]
        )
        
        st.markdown("---")
        
        # Chatbot button
        if st.button("Can I help you? 💬", use_container_width=True):
            st.session_state.show_chatbot = True

    # Check if chatbot was activated
    if st.session_state.get("show_chatbot", False):
        run_chatbot()
    else:
        # Show selected filter view
        if app_selection == "Home":
            st.title("Inflation Rate Analysis")
            st.write(
                "This dashboard compares inflation trends across countries, COVID-era data, regional averages, and war-affected periods. "
                "Use the sidebar to choose the analysis mode and then select countries and dates."
            )
            st.image("world.png", caption="Global inflation overview")
        elif app_selection == "Country Wise":
            run()
        elif app_selection == "During COVID":
            run1()
        elif app_selection == "Region Wise":
            run2()
        elif app_selection == "During War":
            run3()

if __name__ == "__main__":
    main()
