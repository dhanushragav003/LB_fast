

import re
import isodate  

def get_seconds(time_str):
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    else:
        h, m, s = parts
    return h * 3600 + m * 60 + s

def extract_chapters(description,video_duration):
    pattern = re.compile(
        r'(?:.*?)'                                # Anything before timestamp (emojis, text)
        r'(\(?\d{1,2}:\d{2}(?::\d{2})?\)?)'       # Match MM:SS or HH:MM:SS inside optional ()
        r'\s*[-:]?\s*'                            # Separator (dash/colon/space)
        r'([^\n]+)'                               # Capture title until end of line
    )

    chapters = []
    for match in pattern.finditer(description):
        time = match.group(1).strip('()')  # Remove brackets if present
        title = match.group(2).strip()

        # Skip lines with only links
        if 'http' in title.lower():
            continue

        start = get_seconds(time)

        chapters.append({
            'time': time,
            'title': title,
            'start': start
        })

    # Calculate 'end' times for each chapter
    video_duration = isodate.parse_duration(video_duration).total_seconds()
    for i in range(len(chapters)):
        if i + 1 < len(chapters):
            chapters[i]['end'] = chapters[i + 1]['start']
        else:
            chapters[i]['end'] = video_duration  # last chapter ends at video duration
        chapters[i]['index'] = i

    return video_duration,chapters

def split_transcript(text, chunk_size=12000):
    # This splits the string every 12,000 characters
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def stich_chapter_transcript(transcript,chapters):
    chapter_transcripts = []
    current_index = 0
    current_text = ""

    for block in transcript:
        # move to next chapter if needed
        if (
            current_index + 1 < len(chapters)
            and block.start >= chapters[current_index + 1]["start"]
        ):
            chapter_transcripts.append({
                "id": chapters[current_index]["id"],
                "index": chapters[current_index]["index"],
                "title": chapters[current_index]["title"],
                "time": chapters[current_index]["time"],
                "start": chapters[current_index]["start"],
                "end": chapters[current_index]["end"],
                "transcript": current_text.strip(),
            })

            current_index += 1
            current_text = ""

        current_text += block.text + " "

    # append last chapter
    if current_index < len(chapters):
        chapter_transcripts.append({
            "id": chapters[current_index]["id"],
            "index": chapters[current_index]["index"],
            "title": chapters[current_index]["title"],
            "time": chapters[current_index]["time"],
            "start": chapters[current_index]["start"],
            "end": chapters[current_index]["end"],
            "transcript": current_text.strip(),
        })

    return chapter_transcripts


