import streamlit as st
import requests

st.title("Analyst UI")

# Input field for the prompt
prompt = st.text_input("Enter your prompt:", "What is the latest stock price, company information and income statement of Nvidia?")

# Button to submit the prompt
if st.button("Submit"):
    # Make a request to the FastAPI endpoint
    response = requests.post("http://localhost:8000/api/prompt", json={"prompt": prompt}) 

    # Check if the request was successful
    if response.status_code == 200:
        # Access the first dictionary in the list (index 0)
        result_dict = response.json()[0] 
        # Get the value of the 'result' key
        result = result_dict["result"]

        #st.markdown(result)
        st.markdown(
            f'<div style="background-color:#f0f0f5; padding:10px; border-radius:5px;">'
            f'<p style="font-family:sans-serif; font-size:16px; color:#333;">{result}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        
    else:
        st.error(f"Error: {response.status_code}")