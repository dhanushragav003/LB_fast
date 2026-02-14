import requests
from app.helpers import youtube
from app.core.config import app_config
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from supadata import Supadata, SupadataError

supadata = Supadata(api_key=app_config.SUPDATA_KEY)
def get_chapters(video_id):
    try:
        url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={video_id}&key={app_config.YOUTUBE_API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            video_duration = data.get('items',[{}])[0].get('contentDetails',{}).get('duration',"")
            video_title = data.get('items',[{}])[0].get('snippet',{}).get('title',"")
            description = data.get('items',[{}])[0].get('snippet',{}).get('description',"")
            video_duration,chapters = youtube.extract_chapters(description,video_duration)
            result = {
                "title":video_title,
                "resource_type":"video",
                "platform":"youtube",
                "description":description,
                "total_duration_seconds":video_duration,
                "total_chapters":len(chapters),
                "chapters":chapters
            }
            return (response.status_code,result)
        else:
            return (response.status_code,None)
    except Exception as e:
        print(f"YouTube API failed due to {e}")
        return (response.status_code,None)


def get_supadata_transcript(video_id,lan=['en'],is_raw=False):
    try:
        text_transcript = supadata.youtube.transcript(
            video_id=video_id,
        )
        response=[]
        for block in  text_transcript.content:
                content={
                    "text":block.text,
                    "start":int(block.offset)// 1000,
                }
                obj = type('ObjFromDict', (object,), content)
                response.append(obj())
        return response
    except Exception:
        raise 

def get_youtube_transcript(video_id,lan=['en'],is_raw=False):
    try:
        print(video_id)
        ytt_api = YouTubeTranscriptApi()
        transcript=ytt_api.fetch(video_id)
        if is_raw:
            return transcript
        response=""
        for block in transcript:
            response+=block.text.replace("\n", " ")
        return response
    except Exception as e:
        print(f"[ERROR] failed to get_youtube_transcript..",e)
        return get_supadata_transcript(video_id,lan,is_raw)

def get_chapter_transcript(chapters, video_id, ln=["en"]):
    transcript = get_youtube_transcript(video_id, ln, is_raw=True)
    chapter_transcripts= youtube.stich_chapter_transcript(transcript,chapters)
    return chapter_transcripts