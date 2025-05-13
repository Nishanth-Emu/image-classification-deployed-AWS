import streamlit as st
import requests
from PIL import Image
import io
import json

st.title("Fruit Image Classifier")

uploaded_file = st.file_uploader("Upload an image...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)

    if st.button("Predict"):
        files = {"file": ("uploaded_image", uploaded_file.getvalue(), uploaded_file.type)}
        try:
            response = requests.post("http://127.0.0.1:8000/predict/", files=files)
            response.raise_for_status() 
            prediction = response.json()
            st.write(f"Predicted Class: **{prediction['predicted_class']}**")
            st.write(f"Confidence: **{prediction['confidence']:.2f}**")
        except requests.exceptions.RequestException as e:
            st.error(f"Error making prediction: {e}")
            try:
                error_json = response.json()
                st.error(f"API Error Details: {error_json}")
            except (json.JSONDecodeError, AttributeError):
                pass # No JSON error details to display
        except Exception as e:
            st.error(f"Error processing prediction response: {e}")