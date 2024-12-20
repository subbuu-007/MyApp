import streamlit as st
import os
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
from io import BytesIO
from fpdf import FPDF

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Base prompt for summarization
base_prompt = """
You are a YouTube video summarizer. You will take the transcript text and summarize 
the entire video. Please provide the summary of the text given here:
"""

# Function to extract video ID from URL
def extract_video_id(youtube_url):
    try:
        # Match common YouTube URL formats
        pattern = r"(?:v=|youtu\.be/|embed/|v/|watch\?v=|shorts/|e/|^)([A-Za-z0-9_-]{11})"
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
        else:
            st.error("Invalid YouTube URL. Please enter a valid link.")
            return None
    except Exception as e:
        st.error(f"Error parsing YouTube URL: {e}")
        return None

# Function to extract transcript details
def extract_transcript_details(video_id):
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry["text"] for entry in transcript_data])
        return transcript
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

# Function to generate summary using AI
def generate_genmini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

# Function to generate PDF
def generate_pdf(summary_text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, summary_text)
    return pdf.output(dest="S").encode("latin1")

# Streamlit app
st.title("YouTube Summarizer")

# User input for YouTube link
youtube_link = st.text_input("Enter YouTube Video Link")

# User input for summary size
summary_size = st.number_input(
    "Enter the desired summary size in words:",
    min_value=100,
    max_value=2000,
    step=50,
    value=1000
)

# Adjust the prompt based on input size
summary_prompt = base_prompt + f" in {summary_size} words:"

# Display video thumbnail if valid
if youtube_link:
    video_id = extract_video_id(youtube_link)
    if video_id:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

# Button to get detailed notes
if st.button("Get Detailed Notes"):
    if video_id:
        transcript_text = extract_transcript_details(video_id)
        if transcript_text:
            summary = generate_genmini_content(transcript_text, summary_prompt)
            if summary:
                st.subheader("Video Summary")
                st.write(summary)

                # Provide download options
                col1, col2 = st.columns(2)
                with col1:
                    # Download as TXT
                    txt_data = BytesIO()
                    txt_data.write(summary.encode("utf-8"))
                    txt_data.seek(0)
                    st.download_button(
                        label="Download as TXT",
                        data=txt_data,
                        file_name="summary.txt",
                        mime="text/plain"
                    )
                with col2:
                    # Download as PDF
                    pdf_data = BytesIO(generate_pdf(summary))
                    st.download_button(
                        label="Download as PDF",
                        data=pdf_data,
                        file_name="summary.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("Failed to generate summary. Please try again.")
