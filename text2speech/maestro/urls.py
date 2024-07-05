from django.urls import path
from .views import AudioToTextView, NotesToSummaryView

urlpatterns = [
    path('audio-to-text/', AudioToTextView.as_view(), name='audio-to-text'),
    path('notes-to-summary/', NotesToSummaryView.as_view(), name='notes-to-summary'),
]