from fastapi import APIRouter , Depends , Request
from app.services import   llm , qstash , email , youtube
from app.helpers.mail_template import construct_mail , get_completed_mail , get_custom_mail
from starlette.responses import JSONResponse
from app.dependency.database import get_db
from app.dependency.auth import get_current_user
from app.dependency.qstash import verify_qstash_request
from fastapi.encoders import jsonable_encoder
from app.services import db
from app.helpers import tasks
from app.schemas.dailybite import DailyBiteRequest , Dailybite
route=APIRouter(
    prefix="/daliybite",
    tags=["daliybite"]
)

@route.post("/create")
async def create_dailybite(request:DailyBiteRequest,current_user=Depends(get_current_user),session=Depends(get_db)):
    try:
        print(f"{request = }")
        db_session=db.db_session(session)
        chapter,progress=db.get_next_chapter(db_session,request.payload['ulp_id'])
        user_lp=db.fetch_progress(db_session,request.payload['ulp_id'])
        if not (user_lp and user_lp.get('user_id',None) and user_lp.get('user_id',None)==current_user.id):
            return JSONResponse(status_code=403,content={"data":None,"msg": "Not authorized","success":False})
        job_id = user_lp.get('job_id',None) if user_lp.get('daily_bite_enabled',False) else None
        if not chapter.get('transcript',None):
            chapters=db.fetch_resource_chapters(db_session,chapter.get('learning_resource_id',None))
            transcript= youtube.get_chapter_transcript(chapters,chapter.get('learning_resource_id',None))
            db.update_trancripts(db_session,transcript)
        scheduler=qstash.schedule_task()
        request.payload['user_id']=current_user.id
        cron_exp=tasks.build_cron_expression(request.time,request.frequency,request.time_zone)
        job_id=scheduler.create_schedule({"payload":request.payload},request.destination,cron_exp,schedule_id=job_id)
        #update progress
        db.update_dailybite(db_session,progress.get('user_learning_progress_id',None),{"job_id":job_id,'daily_bite_enabled':True})
        play_url=f"{request.payload.get('redirect_url')}/learn?video_id={chapter.get('learning_resource_id',None)}&start=0" if request.payload.get('redirect_url',None) else None
        chapter_resource=db.fetch_learning_resource(db_session,chapter.get('learning_resource_id',None))
        params={
            "scheduled_time":request.time,
            "frequency":request.frequency,
            "play_url":play_url
        }
        subject,body=get_custom_mail(chapter_resource.get('title',''),params,'created')
        subject = subject.replace('Update','scheduled')
        email.send_email(request.payload.get('email',None),subject,html=body)
        return JSONResponse(status_code=200,content=jsonable_encoder({"data":{"job_id":job_id},"msg": "job scheduled","success":True}))
    
    except Exception as e:
        return JSONResponse(status_code=500,content={"data":None,"msg": f"[ERROR] due to {e}","success":False})
@route.delete('/delete')
def delete_dailybite(ulp:int,current_user=Depends(get_current_user),session=Depends(get_db)):
    db_session=db.db_session(session)
    user_lp=db.fetch_progress(db_session,ulp)
    if not (user_lp and user_lp.get('user_id',None) and user_lp.get('user_id',None)==current_user.id):
        return JSONResponse(status_code=403,content={"data":None,"msg": "Not authorized","success":False})
    job_id = user_lp.get('job_id',None) if user_lp.get('daily_bite_enabled',False) else None
    if not job_id : return JSONResponse(status_code=404,content={"data":None,"msg": "job_id not found","success":False})
    scheduler=qstash.schedule_task()
    scheduler.delete_schedule(job_id)
    return JSONResponse(status_code=200,content=jsonable_encoder({"data":None,"msg": "schedule deleted","success":True}))


@route.post('/send')
async def send_bite(request:Dailybite,session=Depends(get_db)):#request: bytes = Depends(verify_qstash_request)
    try:
        if not (request.payload.get('ulp_id',None) and request.payload.get('email',None)):
            return JSONResponse(status_code=500,content={"data":None,"msg": "missing ulp_id or email to processs","success":False})
        db_session= db.db_session(session)
        ulp_id=request.payload.get('ulp_id')
        to_mail=request.payload.get('email',None)
        next_chapter,progress= db.get_next_chapter(db_session,int(ulp_id))
        if not next_chapter:
            progress=db.fetch_progress(db_session,ulp_id)
            resource=db.fetch_learning_resource(db_session,progress.get('learning_resource_id',None))
            job_id=progress['job_id']
            print(f"{job_id = }")
            redirect_url=f"{request.payload.get('redirect_url')}/learn?video_id={next_chapter.get('learning_resource_id',None)}" if request.payload.get('redirect_url',None) else None
            params={ "completed_chapters":progress.get('completed_chapters'),"play_url":redirect_url}
            subject,body=get_custom_mail(resource.get('title',None),params,'completed')
        else:
            chapter_resource=db.fetch_learning_resource(db_session,next_chapter.get('learning_resource_id',None))
            resource_title=chapter_resource.get('title',None)
            chapter_title=next_chapter.get('title',None)
            transcript = next_chapter.get('transcript',None)
            print(f"{next_chapter['id'] = } ")
            print(f"{progress.get('id',None) = }")
            if not (resource_title and chapter_title and transcript):
                return JSONResponse(status_code=404,content=jsonable_encoder({"data":None,"msg": "metadata missing","success":False}))
            redirect_url=f"{request.payload.get('redirect_url')}/learn?video_id={next_chapter.get('learning_resource_id',None)}&start={next_chapter.get('start',0)}" if request.payload.get('redirect_url',None) else None
            #generate llm content
            bitemail=await llm.fetch_Bite_email(resource_title,chapter_title,transcript)
            subject,body=construct_mail(bitemail,redirect_url)
        email.send_email(to_mail,subject,html=body)
        if next_chapter:
            db.mark_chapter_watched(db_session,progress.get('id',None))
            return JSONResponse(status_code=200,content=jsonable_encoder({"data":jsonable_encoder(bitemail),"msg": "generated content","success":True}))
        else:
            scheduler=qstash.schedule_task()
            scheduler.delete_schedule(job_id)
            return JSONResponse(status_code=200,content=jsonable_encoder({"data":None,"msg": "schedule deleted","success":True}))
    except Exception as e:
        return JSONResponse(status_code=500,content=jsonable_encoder({"data":None,"msg": str(e),"success":False}))

    