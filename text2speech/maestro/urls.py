from django.urls import path
from .views import AudioToTextView

urlpatterns = [
    path('audio-to-text/', AudioToTextView.as_view(), name='audio-to-text'),
]


from . import views

urlpatterns = [
    path('process-meeting/', views.process_meeting, name='process_meeting'),
]