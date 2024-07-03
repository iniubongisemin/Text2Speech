from django.db import models

class Meeting(models.Model):
    audio_file = models.FileField(upload_to='meetings/')
    transcription = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    action_items = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"Meeting {self.id}"