from app.services.llm import summary_generator
import json

async def stream_transcript_summaries(chapter_transcripts: list):
    """
    Generator that yields each chapter dict with summary
    after the summary is generated.
    """
    try:
        for chapter in chapter_transcripts:
            transcript = chapter.pop("transcript", "")
            summary = await summary_generator(transcript)
            print(summary)
            chapter["summary"] = summary
            yield f"data: {json.dumps(chapter)}\n\n"
    except Exception as e:
        print("STREAM ERROR:", e)
        yield f"event: error\ndata: {str(e)}\n\n"
    yield "event: done\ndata: true\n\n"
