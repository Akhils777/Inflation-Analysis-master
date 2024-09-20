import streamlit as st
from app.app import run
from app.app1 import run1
from app.app2 import run2
from app.app3 import run3

def main():
    app_selection = st.sidebar.selectbox("Select App", ["Home", "app", "app1", "app2", "app3"])

    if app_selection == "Home":
        st.title("Inflation rate analysis")

    if app_selection == "Home":
        st.write("Welcome. Choose an app from the sidebar.")
        st.image("world.png", caption="World Image", use_column_width=True)
    elif app_selection == "app":
        run()
    elif app_selection == "app1":
        run1()
    elif app_selection == "app2":
        run2()
    elif app_selection == "app3":
        run3()

if __name__ == "__main__":
    main()
