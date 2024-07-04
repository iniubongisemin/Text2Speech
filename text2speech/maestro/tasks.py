import os
import requests

def process_audio_file(file_path):
    whisper_api_url = os.environ.get('WHISPER_API_URL')
    whisper_api_key = os.environ.get('WHISPER_API_KEY')

    # Making a post request to the whisper API
    with open(file_path, 'rb') as f:
        response = requests.post(
            whisper_api_url,
            headers={'Authorization': f'Bearer {whisper_api_key}'},
            files={'file': f}
        ) 

    if response.status_code == 200:
        text_output = response.json()
        # Further process the text output to generate a detailed summary
        transcript = generate_summary(text_output)
        return transcript
    else:
        return {"error": "Failed to convert audio to text"}

def generate_summary(text_output):
    
    return text_output

