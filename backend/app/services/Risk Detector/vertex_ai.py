#from google.cloud import aiplatform
#from google.cloud.aiplatform import preview
from vertexai.preview.generative_models import GenerativeModel

# Initialize AI Platform (optional global initialization)
#aiplatform.init(project="genai-exhange-hackathon", location="global")

# Import the generative model
#from google.cloud.aiplatform.preview import generative_models

# Setup model handle for Gemini (choose correct version)
model = GenerativeModel("gemini-2.5-flash")

def generate_content(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text