from fastapi import APIRouter , Depends
from app.dependency.database import get_db
from app.dependency.auth import get_current_user , get_optinal_current_user
from app.services import  llm , db , youtube , chapter_service
from app.helpers.quiz import normalize_row
from starlette.responses import JSONResponse
from app.schemas.quiz import QuizRequest  
from fastapi.encoders import jsonable_encoder
from datetime import datetime  ,timezone
from fastapi.responses import StreamingResponse
route=APIRouter(
    prefix="/api",
    tags=["api"]
)


@route.get('/chapters')
def get_context(id:str="",current_user=Depends(get_optinal_current_user),session=Depends(get_db)):
    try:
        db_session= db.db_session(session)
        print(f"{current_user = }")
        with db_session.db.begin():
            if not current_user:
                print("not logged in")
                title,chapters=db.ensure_learning_resource(db_session,id)
                response={
                    "title":title,
                    "chapters":chapters
                }
            else:
                user_id=current_user.id
                title,ulp= db.ensure_user_progress(db_session,user_id,id)
                response={
                    "title":title,
                    "chapters":db_session.get_chapters_with_progress(ulp["id"],id),
                    "success":True
                }
        return JSONResponse(status_code=200,content=jsonable_encoder(response))
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500,content={"msg":str(e),"success":False})


@route.post("/genquiz")
def quiz_generator(QuizRequest: QuizRequest):
    chapter_text = QuizRequest.text
    context = QuizRequest.context
    total_question = QuizRequest.size or 1
    try:
        msg,quiz_data=llm.generate_quiz(chapter_text,context,total_question)
        print(msg,quiz_data)
        if quiz_data:
            return JSONResponse(status_code=200,content=quiz_data)
        if msg:
            return JSONResponse(status_code=500,content={"error": str(msg)})
    except Exception as e:
        return JSONResponse(status_code=500,content={"error": str(e)})
    
@route.get("/sse/genquiz")
async def quiz_generator(text:str,context:str,size:int):
    return StreamingResponse(
        llm.sse_generate_quiz(
            text,
            context,
            size or 1
        ),
        media_type="text/event-stream"
    )


    
@route.post("/submitquiz")
def submitquiz(chapter_progress_id:int,score_percent:float,current_user=Depends(get_current_user),session=Depends(get_db)):
    is_passed= score_percent >= 70
    user_id=current_user.id
    payload={
        "watched":True,
        "quiz_attempted":True,
        "score_percent":score_percent,
        "is_passed":is_passed,
        "attempts_count":1,
        "last_attempt_at":datetime.now(timezone.utc)
    }
    try:
        db_session= db.db_session(session)
        userChapter_progress=db.set_userChapter_progress(db_session,user_id,chapter_progress_id,payload)
        if userChapter_progress:
            return JSONResponse(status_code=200,content=jsonable_encoder({"data":userChapter_progress,"success":True,"msg":None}))
    except Exception as e:
        return JSONResponse(status_code=500,content={"data":None,"msg": str(e),"success":False})
    


@route.get("/yourlearning")
def get_user_progress(is_completed:bool=False,sort_by:str='last_accessed_at',order:str='asc',current_user=Depends(get_current_user),session=Depends(get_db)):
    try:
        db_session= db.db_session(session)
        filters={
            "is_completed":is_completed
        }
        print(current_user.id)
        user_progress=db.get_userprogress(db_session,current_user.id,filters,sort_by,order)
        return JSONResponse(status_code=200,content=jsonable_encoder({"data":user_progress,"success":True,"msg":None}))
    except Exception as e:
        return JSONResponse(status_code=500,content={"data":None,"msg": str(e),"success":False})
    

@route.get("/transcripts")
def fetch_transcript(id:str,session=Depends(get_db)):
    try:
        db_session= db.db_session(session)
        chapters=db.fetch_resource_chapters(db_session,id)
        if not chapters:
            return JSONResponse(status_code=500,content={"data":"no chapters found","msg": str(e),"success":False})
        if not chapters[0].get('transcript',None) :
            print("fetching transcript from youtube lib")
            transcript= youtube.get_chapter_transcript(chapters,id)
            update = db.update_trancripts(db_session,transcript)
            return JSONResponse(status_code=200,content={"data":transcript,"msg": None,"success":True})
        return JSONResponse(status_code=200,content={"data":jsonable_encoder(chapters),"msg": None,"success":True})
    except Exception as e:
        return JSONResponse(status_code=500,content={"data":None,"msg": str(e),"success":False})

@route.get("/chapter_summary")
async def fetch_chapter_summary(id: str, session=Depends(get_db)):
    try:
        db_session= db.db_session(session)
        chapters = db.fetch_resource_chapters(db_session, id)  # List[dict]
        print(chapters) 
        if not chapters[0].get('transcript',None) :
            print("fetching transcript from youtube")
            chapter_transcript= youtube.get_chapter_transcript(chapters,id)
            update = db.update_trancripts(db_session,chapter_transcript)
        else: 
            print("fetched transcript from db")
            chapter_transcript = [normalize_row(chapter) for chapter in chapters]
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"data": chapters, "msg": str(e), "success": False}
        )
    # Stream summaries
    return StreamingResponse(
            chapter_service.stream_transcript_summaries(chapter_transcript),
            media_type="text/event-stream"
        )
    
@route.get("{ucp_id}/watched")
async def mark_chapter_watched(ucp_id:int,current_user=Depends(get_current_user), session=Depends(get_db)):
    try:
        db_session= db.db_session(session)
        db.mark_chapter_watched(db_session,ucp_id)
        return JSONResponse(status_code=200,content={"data":None,"msg": f"{ucp_id} is marked as watched","success":True})
    except  Exception as e:
        return JSONResponse(status_code=200,content={"data":None,"msg": f"{ucp_id} is failed to mark as watched","success":False})






    


