from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
from typing import List

app = FastAPI()

try:
    model = load_model('Fruit_AI/fruit_cnn_model.h5')
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

IMAGE_SIZE = (128, 128) 
CLASS_NAMES = ['apple', 'banana', 'mango', 'orange']  

def preprocess_image(image: Image.Image):
    image = image.resize(IMAGE_SIZE)
    image = np.array(image) / 255.0
    image = np.expand_dims(image, axis=0)
    return image

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    if model is None:
        return JSONResponse(content={"error": "Model not loaded"}, status_code=500)
    try:
        image = Image.open(file.file).convert("RGB")
        processed_image = preprocess_image(image)
        prediction = model.predict(processed_image)
        predicted_class_index = np.argmax(prediction)
        predicted_class_name = CLASS_NAMES[predicted_class_index]
        confidence = float(prediction[0][predicted_class_index])
        return JSONResponse(content={"predicted_class": predicted_class_name, "confidence": confidence})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/")
async def health_check():
    return {"status": "API is running"}