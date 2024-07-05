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
    def post(self, request, *args, **kwargs):
        transcription = request.data.get('text')
        if not transcription:
            return Response({'error': 'Transcribed text is required please ensure that your audio is transcribed first'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Generating meeting summary
            # summary_prompt = f"Please provide a detailed summary of the following meeting transcription:\n\n{transcription['text']} in JSON format with the key being 'meeting_summary'"
            summary_prompt = f"Please provide a detailed summary of the following meeting transcription:\n\n{transcription} in JSON format with the key being 'meeting_summary'"
            summary_response = gpt_orchestrator(transcription, summary_prompt)
            # meeting_summary = summary_response.get('meeting_summary')

            print(f"Summary response: {summary_response}")

            if isinstance(summary_response, str):
                summary_response = json.loads(summary_response)

            meeting_summary = summary_response.get("meeting_summary")

            if not meeting_summary:
                return Response({'error': 'Failed to generate meeting summary'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Generating action items
            action_items_prompt = f"""Based on the following meeting summary, please create a list of action items with their respective timelines:

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
            action_items_response = gpt_sub_agent(meeting_summary, action_items_prompt)

            print(f"Action items response: {action_items_response}")
            
            if isinstance(action_items_response, str):
                action_items_response = json.loads(action_items_response)

            action_items = action_items_response.get('action_items')

            if not action_items:
                return Response({'error': 'Failed to generate action items'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Refining and further optimizing action items
            refine_prompt = f"Further refine and optimize the action_items initially obtained and return a final output"
            refined_output = openai_refine(action_items, refine_prompt)

            print(f"Refined output: {refined_output}")

            if isinstance(refined_output, str):
                refined_output = json.loads(refined_output)

            # Preparing the final response
            final_response = {
                'meeting_summary': meeting_summary,
                'action_items': action_items,
                'refined_output': refined_output,
            }

            return Response(final_response, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
