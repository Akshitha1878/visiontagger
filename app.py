import streamlit as st
import google.generativeai as genai
import os
import json
import io
import pyttsx3
import threading
from PIL import Image
from dotenv import load_dotenv

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure API
if not GEMINI_API_KEY:
    st.error(" API Key not found! Please set it in your .env file.")
    st.stop()
genai.configure(api_key=GEMINI_API_KEY)

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Adjust speech rate
engine.setProperty('volume', 1)  # Set volume level

# Function to analyze image
def analyze_image(image):
    try:
        img_byte_arr = io.BytesIO()
        image_format = image.format if image.format else "PNG"  # Preserve format
        image.save(img_byte_arr, format=image_format)
        img_byte_arr = img_byte_arr.getvalue()

        # Use the latest Gemini AI model
        model = genai.GenerativeModel("gemini-1.5-pro")

        # Send high-quality image to Gemini AI
        response = model.generate_content([image], stream=False)

        if hasattr(response, "text") and response.text.strip():
            metadata = response.text.strip()
            try:
                metadata_json = json.loads(metadata)
                return metadata_json
            except json.JSONDecodeError:
                return metadata  # Return as plain text if not valid JSON
        else:
            return "Unexpected API response format."

    except Exception as e:
        return f"Error processing image: {e}"

# Function to convert text to speech and save as MP3
def text_to_speech(text, filename="metadata_audio.mp3"):
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)
    tts_engine.setProperty('volume', 1)
    tts_engine.save_to_file(text, filename)
    tts_engine.runAndWait()
    return filename

# Streamlit App
st.title("🔍 VisionTagger AI")

#  Allow multiple file uploads
uploaded_files = st.file_uploader("📤 Upload Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)

        #  Display each image
        st.image(image, caption=f"📸 {uploaded_file.name}", use_column_width=False)

        st.subheader("🧐 Analyzing Image...")
        with st.spinner("⚡ Processing..."):
            metadata_text = analyze_image(image)

        if isinstance(metadata_text, str) and metadata_text.startswith("Error"):
            st.error(f" {metadata_text}")
        else:
            st.subheader("📄 Image Description")
            st.write(metadata_text)

            # Provide a text file download option
            metadata_filename = "metadata.txt"
            with open(metadata_filename, "w") as f:
                f.write(str(metadata_text))

            st.download_button(
                label="📄 Download Metadata as Text File",
                data=open(metadata_filename, "rb"),
                file_name=metadata_filename,
                mime="text/plain"
            )

            # Convert metadata to speech and provide MP3 download
            mp3_filename = text_to_speech(str(metadata_text))

            with open(mp3_filename, "rb") as file:
                st.download_button(
                    label="🔊 Download Audio Description",
                    data=file,
                    file_name="image_description.mp3",
                    mime="audio/mp3"
                )

            # Speak the metadata aloud
            st.subheader("🔊 Listening...")
            threading.Thread(target=text_to_speech, args=(str(metadata_text),), daemon=True).start()
