from django.http import JsonResponse
import pdfplumber
from transformers import pipeline
import re
from django.shortcuts import render

# Load translation model
translator = pipeline("translation", model="facebook/m2m100_418M")

def clean_text(text):
    """ Remove extra spaces, new lines, and unnecessary characters. """
    return re.sub(r'\s+', ' ', text).strip()

def split_text(text, max_length=400):
    """ Split long text into smaller chunks for translation """
    words = text.split()
    chunks = []
    chunk = []
    char_count = 0

    for word in words:
        if char_count + len(word) < max_length:
            chunk.append(word)
            char_count += len(word) + 1  # +1 for space
        else:
            chunks.append(" ".join(chunk))
            chunk = [word]
            char_count = len(word)
    
    if chunk:
        chunks.append(" ".join(chunk))
    
    return chunks

def translate_text(text):
    """ Translate text with proper handling for long inputs """
    text = clean_text(text)
    
    if len(text.split()) > 400:  # If too long, split into chunks
        text_chunks = split_text(text, max_length=400)
        translated_chunks = [
            translator(chunk, src_lang="en", tgt_lang="tr", max_length=500)[0]['translation_text']
            for chunk in text_chunks
        ]
        translated_text = " ".join(translated_chunks)
    else:
        translated_text = translator(text, src_lang="en", tgt_lang="tr", max_length=500)[0]['translation_text']
    
    return translated_text


def translate_page(request):
    """ Render translation page. """
    return render(request, "translate.html")

def process_translation(request):
    """ Handle text input translation """
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if not text:
            return JsonResponse({"error": "No text provided!"}, status=400)
        
        translated_text = translate_text(text)
        return JsonResponse({"translated_text": translated_text})

def upload_file(request):
    """ Handle PDF file uploads and extract text for translation """
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        file_ext = uploaded_file.name.split('.')[-1].lower()

        if file_ext not in ["pdf", "txt"]:
            return JsonResponse({"error": "Only PDF and TXT files are supported!"}, status=400)
        
        extracted_text = ""

        if file_ext == "pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                extracted_text = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif file_ext == "txt":
            extracted_text = uploaded_file.read().decode("utf-8")

        extracted_text = clean_text(extracted_text)

        if not extracted_text:
            return JsonResponse({"error": "No readable text found in the document!"}, status=400)

        translated_text = translate_text(extracted_text)
        return JsonResponse({"translated_text": translated_text})

    return JsonResponse({"error": "Invalid request!"}, status=400)
