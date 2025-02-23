from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

def welcome_page(request):
    return render(request, "index.html")  # This will load index.html

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', welcome_page, name='home'),  # Main welcome page
    path('translate/', include('translator.urls')),  # Translation page
]
