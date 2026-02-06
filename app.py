# this is for testing
import streamlit as st
import pandas as pd

# Title
st.title("🍎 Interactive Fruit Explorer")
st.write("Explore your favorite fruits and learn some fun facts!")

# Sample data
data = {
    "Fruit": ["Apple", "Banana", "Orange", "Strawberry", "Mango"],
    "Color": ["Red", "Yellow", "Orange", "Red", "Yellow"],
    "Calories per 100g": [52, 96, 47, 33, 60]
}

df = pd.DataFrame(data)

# Sidebar selection
selected_fruit = st.sidebar.selectbox("Select a fruit", df["Fruit"])

# Display fruit info
fruit_info = df[df["Fruit"] == selected_fruit]
st.subheader(f"{selected_fruit} Info")
st.write(fruit_info)

# Fun fact
fun_facts = {
    "Apple": "Apples float in water because they are 25% air!",
    "Banana": "Bananas are berries, but strawberries are not!",
    "Orange": "Oranges are actually modified berries called hesperidium.",
    "Strawberry": "Strawberries have seeds on the outside.",
    "Mango": "Mangoes are known as the 'king of fruits'."
}

st.info(fun_facts[selected_fruit])

# Input from user
st.subheader("Your Fruit Opinion")
user_input = st.text_input("What do you think about this fruit?")
if user_input:
    st.write("You said:", user_input)
