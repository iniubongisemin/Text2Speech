from django.urls import path
from .views import AudioToTextView, NotesToSummary

urlpatterns = [
    path('audio-to-text/', AudioToTextView.as_view(), name='audio-to-text'),
    path('notes-to-summary/', NotesToSummary.as_view(), name='notes-to-summary'),
]