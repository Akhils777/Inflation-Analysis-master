import streamlit as st
from app.app import run
from app.app1 import run1
from app.app2 import run2
from app.app3 import run3

def main():
    app_selection = st.sidebar.selectbox("Select Filter", ["Home", "Country Wise", "During COVID", "Region Wise", "During War"])

    if app_selection == "Home":
        st.title("Inflation rate analysis")

    if app_selection == "Home":
        st.write("Welcome. Choose an app from the sidebar.")
        st.image("world.png", caption="World Image", use_container_width=True)
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
