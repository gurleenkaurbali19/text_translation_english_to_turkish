from django.urls import path
from .views import process_translation, upload_file, translate_page  # Import the function

urlpatterns = [
    path('', translate_page, name='translate_page'),  # Loads translate.html
    path('process/', process_translation, name='process_translation'),  # ✅ For text input
    path('upload/', upload_file, name='upload_file'),  # ✅ For file upload
]
