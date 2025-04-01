import os
import base64
import requests
import logging
from PIL import Image
from io import BytesIO

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .forms import ImageForm


logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def index(request):
    form = ImageForm()
    return render(request, 'groq_vision/index.html', {'form': form})

def process_image(image_path, query):
    try:
        with open(image_path, 'rb') as image_file:
            image_content = image_file.read()
            encoded_image = base64.b64encode(image_content).decode("utf-8")
        
        try:
            img = Image.open(BytesIO(image_content))
            img.verify()
        except Exception as e:
            logger.error(f"Invalid image format: {str(e)}")
            return {"error": f"Invalid image format: {str(e)}"}
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]
            }
        ]
        
        response = requests.post(
            GROQ_API_URL,
            json={
                "model": "llama-3.2-90b-vision-preview",
                "messages": messages,
                "max_tokens": 1000
            },
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            logger.info(f"Processed response: {answer}")
            return answer
        else:
            logger.error(f"Error from API: {response.status_code} - {response.text}")
            return f"Error from API: {response.status_code}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

def process_text(query):
    try:
        messages = [{"role": "user", "content": query}]
        
        response = requests.post(
            GROQ_API_URL,
            json={
                "model": "llama-3.2-3b-preview",
                "messages": messages,
                "max_tokens": 1000
            },
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            logger.info(f"Processed text response: {answer}")
            return answer
        else:
            logger.error(f"Error from API: {response.status_code} - {response.text}")
            return f"Error from API: {response.status_code}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

@csrf_exempt
def process_image_view(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            query = form.cleaned_data['query']
            
            if 'image' in request.FILES:
                image = request.FILES['image']
                path = default_storage.save('tmp/' + image.name, ContentFile(image.read()))
                temp_file = os.path.join(settings.MEDIA_ROOT, path)
                response = process_image(temp_file, query)
                default_storage.delete(path)
                
                return JsonResponse({'response': response})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def process_text_view(request):
    if request.method == 'POST':
        form = ImageForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            response = process_text(query)
            return JsonResponse({'response': response})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)