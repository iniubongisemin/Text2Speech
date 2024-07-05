from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
# from .models import Meeting
# from .serializers import MeetingSerializer
import requests
from django.conf import settings
import os 
import tempfile
from openai import OpenAI
import json
from .maestro import gpt_orchestrator, gpt_sub_agent, openai_refine
# from .tasks import process_audio_file

class AudioToTextView(APIView):

    def post(self, request, *args, **kwargs):
        if 'audio_file' not in request.FILES:
            return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        audio_file = request.FILES['audio_file']

        # Saving the temporary file 
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            transcription = self.convert_audio_to_text(temp_file_path)
        finally:
            # Cleaning up the temporary file
            os.remove(temp_file_path)
        
        # Creating and saving the meeting with the transription
        # meeting = Meeting.objects.create(audio_file=audio_file, transcription=transcription['text'])
        return Response(transcription, status=status.HTTP_201_CREATED)
    

        # serializer = MeetingSerializer(meeting)
        # return Response(serializer.data, status=status.HTTP_201_CREATED)

    def convert_audio_to_text(self, audio_file_path):
        url = "https://api.lemonfox.ai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {settings.WHISPER_API_KEY}"
        }

        with open(audio_file_path, "rb") as audio_file:
            files = {"file": audio_file}
            response = requests.post(url, headers=headers, files=files)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error in API call: {response.status_code} - {response.text}")


class NotesToSummaryView(APIView):
    def post(self, request, transcription, meeting_summary, refined_output, *args, **kwargs):
        transcription = request.data.get('text')
        if not transcription:
            return Response({'error': 'Transcribed text is required please ensure that your audio is transcribed first'})
        try:
            prompt = f"Please provide a detailed summary of the following meeting transcription:\n\n{transcription['text']} in JSON format with the key being 'meeting_summary'"
            response = gpt_orchestrator(transcription, prompt)
            if response.status_code == 200:
                return response.json()
            
            meeting_summary = request.data.get('meeting_summary')
            if not meeting_summary:
                return Response({'error': 'Meeting summary is required to proceed'})

            sub_agent = gpt_sub_agent(meeting_summary, prompt)
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
            response = sub_agent

            if response.status_code == 200:
                return response.json
        finally:
            prompt = "Further refine and optimize the action_items initially obtained and return a final output"
            refined_output = request.data.get('action_items')
            if not refined_output:
                return Response({'error': 'Refined Final Output is required'})
            refiner = openai_refine(refined_output, prompt)
            
            response = refiner
            if response.status_code == 200:
                return response.json







    # def generate_meeting_summary(transcription):
        # client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # prompt = f"Please provide a detailed summary of the following meeting transcription:\n\n{transcription['text']}"

        # response = gpt_orchestrator(transcription, prompt)
        # response = client.chat.completions.create(
        #     model="gpt-4o",
        #     messages=[
        #         {"role": "system", "content": "You are an AI assistant that summarizes meeting transcriptions."},
        #         {"role": "user", "content": prompt}
        #     ],
        #     max_tokens=1000
        # )

        # return response.choices[0].message.content
        # if response.status_code == 200:
        #     return response.json()

    # def create_action_items(meeting_summary):
        # client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # prompt = f"""Based on the following meeting summary, please create a list of action items with their respective timelines:

        # {meeting_summary}

        # Format the output as a JSON object with the following structure:
        # {{
        #     "action_items": [
        #         {{
        #             "task": "Task description",
        #             "assignee": "Person responsible",
        #             "deadline": "YYYY-MM-DD"
        #         }}
        #     ]
        # }}
        # """
        # response = gpt_sub_agent(meeting_summary, prompt)
        # response = client.chat.completions.create(
        #     model="gpt-4o",
        #     messages=[
        #         {"role": "system", "content": "You are an AI assistant that extracts action items from meeting summaries."},
        #         {"role": "user", "content": prompt}
        #     ],
        #     max_tokens=1000
        # )
        # return json.loads(response.choices[0].message.content)

        # if response.status_code == 200:
        #     return json.loads(response.choices[0].message.content)
