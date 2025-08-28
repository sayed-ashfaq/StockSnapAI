import streamlit as st

# Page config
st.set_page_config(page_title="My Search App", page_icon="🔎", layout="wide")

# Add some vertical space to center content
st.markdown("<br><br><br>", unsafe_allow_html=True)

# Center align title
st.markdown(
    "<h1 style='text-align: center;'>Stock Snap AI</h1>",
    unsafe_allow_html=True
)

# Add space between title and input box
st.markdown("<br>", unsafe_allow_html=True)


# Center the input field using columns
col1, col2, col3 = st.columns([1,2,1])  # adjust ratio
with col2:
    search_query = st.text_input("", placeholder="Enter the stock name...", label_visibility="collapsed")

# Handle search
if search_query:
    st.write(f"🔍 You searched for: **{search_query}**")

# # Custom CSS for background
# page_bg = """
# <style>
# .stApp {
#     background-color: #e6f2ff;   /* light blue */
# }
# </style>
# """
# st.markdown(page_bg, unsafe_allow_html=True)