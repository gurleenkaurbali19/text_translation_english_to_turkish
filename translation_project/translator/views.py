import os
import torch
import pdfplumber
import textstat
from django.shortcuts import render
from django.http import JsonResponse
from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
from sentence_transformers import SentenceTransformer, util
from django.views.decorators.csrf import csrf_exempt

# Load models
translator = pipeline("translation", model="facebook/m2m100_418M")
perplexity_model = GPT2LMHeadModel.from_pretrained("gpt2")
perplexity_tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
similarity_model = SentenceTransformer("all-MiniLM-L6-v2")

def calculate_perplexity(text):
    """Computes Perplexity Score using GPT-2."""
    encodings = perplexity_tokenizer(text, return_tensors="pt")
    input_ids = encodings.input_ids
    with torch.no_grad():
        outputs = perplexity_model(input_ids, labels=input_ids)
        loss = outputs.loss
    return torch.exp(loss).item()

def calculate_readability(text):
    """Computes Readability Score using textstat."""
    return textstat.flesch_reading_ease(text)

def calculate_semantic_similarity(original, translated):
    """Computes Semantic Similarity Score using Sentence Transformers."""
    embeddings = similarity_model.encode([original, translated], convert_to_tensor=True)
    score = util.pytorch_cos_sim(embeddings[0], embeddings[1])
    return score.item()

def evaluate_translation(source, translated):
    """Computes evaluation metrics using user's calculation logic."""
    perplexity_score = calculate_perplexity(translated)
    readability_score = calculate_readability(translated)
    semantic_similarity_score = calculate_semantic_similarity(source, translated)

    # Normalize rating based on similarity
    rating = min(10, max(0, round(semantic_similarity_score * 10, 1)))  

    return {
        "perplexity_score": round(perplexity_score, 2),
        "readability_score": round(readability_score, 2),
        "semantic_similarity_score": round(semantic_similarity_score, 3),
        "rating_out_of_10": rating
    }

def extract_text_from_pdf(pdf_file):
    """Extracts text from uploaded PDF."""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

@csrf_exempt
def translate_text(request):
    """Handles text and PDF translation requests."""
    if request.method == "POST":
        input_text = request.POST.get("text", "")
        uploaded_file = request.FILES.get("file")

        # Handle PDF file input
        if uploaded_file and uploaded_file.name.endswith(".pdf"):
            input_text = extract_text_from_pdf(uploaded_file)

        if not input_text.strip():
            return JsonResponse({"error": "No input text provided."}, status=400)

        # Translate text
        translated_text = translator(input_text, src_lang="en", tgt_lang="tr")[0]['translation_text']

        # Evaluate translation
        scores = evaluate_translation(input_text, translated_text)

        return JsonResponse({
            "translated_text": translated_text,
            "evaluation_scores": scores
        })

    return render(request, "translate.html")
