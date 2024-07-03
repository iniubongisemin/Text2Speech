import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
import requests
from dotenv import load_dotenv
load_dotenv()

from .tasks import process_audio_file

class AudioToTextView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES['file']
        
        # Saving the file locally 
        file_path = f'tmp/{file_obj.name}'
        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # Calling the whisper API to convert the given audio to text
        text_output = process_audio_file(file_path)

        # Delete the temporary file
        os.remove(file_path)

        return Response(text_output, status=status.HTTP_200_OK)
    

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Meeting
from .serializers import MeetingSerializer
import requests
import json
from django.conf import settings
    
@api_view(['POST'])
def process_meeting(request):
    if 'audio_file' not in request.FILES:
        return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)

    audio_file = request.FILES['audio_file']
    meeting = Meeting.objects.create(audio_file=audio_file)

    # Step 1: Convert audio to text
    transcription = convert_audio_to_text(meeting.audio_file.path)
    meeting.transcription = transcription['text']

    # Step 2: Generate meeting summary
    meeting.summary = generate_meeting_summary(transcription)

    # Step 3: Create action items
    meeting.action_items = create_action_items(meeting.summary)

    meeting.save()

    serializer = MeetingSerializer(meeting)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

def convert_audio_to_text(audio_file_path):
    url = "https://api.lemonfox.ai/v1/whisper"
    headers = {
        "Authorization": f"Bearer {settings.LEMONFOX_API_KEY}"
    }
    
    with open(audio_file_path, "rb") as audio_file:
        files = {"file": audio_file}
        response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error in API call: {response.status_code} - {response.text}")

def generate_meeting_summary(transcription):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"Please provide a detailed summary of the following meeting transcription:\n\n{transcription['text']}"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI assistant that summarizes meeting transcriptions."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def create_action_items(meeting_summary):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"""Based on the following meeting summary, please create a list of action items with their respective timelines:

    {meeting_summary}

    Format the output as a JSON object with the following structure:
    {{
        "action_items": [
            {{
                "task": "Task description",
                "assignee": "Person responsible",
                "deadline": "YYYY-MM-DD"
            }}
        ]
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI assistant that extracts action items from meeting summaries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    
    return json.loads(response.choices[0].message.content)
