import streamlit as st
import joblib
import pandas as pd

# Load model
model = joblib.load("model.pkl")

# Title
st.title("📊 Student Marks Predictor")

st.write("Enter study hours to predict marks")

# Input
hours = st.number_input("Study Hours", min_value=0.0, max_value=12.0, step=0.5)

# Button
if st.button("Predict"):
    input_data = pd.DataFrame([[hours]], columns=['Hours'])
    prediction = model.predict(input_data)

    st.success(f"Predicted Marks: {prediction[0]:.2f}")