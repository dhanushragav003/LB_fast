from sqlalchemy.orm import Session 
from sqlalchemy import delete ,select , asc , desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert 
from app.models.User import User
from sqlalchemy.inspection import inspect
from sqlalchemy import update
from app.services.youtube import get_chapters
from app.models.learning import LearningResource , LearningResourceChapter , UserChapterProgress , UserLearningProgress
from app.integrations.db import db_session

def upsert_record(db: Session,**kwargs):
    username=kwargs.get("username")
    data = {k: v for k, v in kwargs.items() if k != 'user_id' and v is not None}
    stmt = insert(User).values(data)
    update_cols = {
        key: stmt.excluded[key] 
        for key in kwargs.keys()
    }
    stmt= stmt.on_conflict_do_update(
        index_elements=['username'],
        set_=update_cols,

    ).returning(User)
    result = db.execute(stmt)
    db.commit()
    
    return result.scalar_one()

class db_session():
    def __init__(self,db:Session):
        self.db=db
    def execute_stmt(self, stmt, *, scalar=False, first=False):
        try:
            result = self.db.execute(stmt)

            if scalar and first:
                return result.scalars().first()

            if scalar:
                return result.scalars().all()

            if first:
                return result.first()

            return result.fetchall()

        except Exception as e:
            raise e

    def get_record(
    self,
    model,
    filters,
    join_table=None,
    join_on=None,              # explicit join condition
    order_col=None,
    order_fn=asc,
    first_only=True
    ):
        try:
            table = model.__table__ if hasattr(model, "__table__") else model


            # JOIN
            if join_table is not None and join_on is not None:
                stmt=select(table,join_table)
                stmt = stmt.join(join_table, join_on)
            else:
                stmt = select(table)
            # FILTERS
            if filters:
                for col, value in filters.items():
                    stmt = stmt.where(getattr(model, col) == value)

            # ORDER
            if order_col is not None:
                stmt = stmt.order_by(order_fn(order_col))

            result = self.db.execute(stmt)

            if first_only:
                return result.mappings().fetchone()
            
            return result.mappings().fetchall()
        except Exception as e:
            raise RuntimeError("Database fetch failed") from e
    def update_by_id(self, model, id, payload,commit=True):
        try:
            table = model.__table__ if hasattr(model, "__table__") else model
            print(f"Updating record in {table} with {id}")

            # Get primary key
            mapper = inspect(table)
            pk_names = {c.name for c in mapper.primary_key}
            if len(pk_names) != 1:
                raise ValueError("update_by_id currently only supports single-column primary keys")
            pk_name = list(pk_names)[0]

            # Remove PK from payload
            update_payload = {k: v for k, v in payload.items() if k not in pk_names}
            if not update_payload:
                return None

            # Build statement
            stmt = (
                update(table)
                .where(getattr(table.c, pk_name) == id)
                .values(**update_payload)
                .returning(table)
            )

            # Execute
            result = self.db.execute(stmt)
            row = result.fetchone()
            if commit:
                self.db.commit()
            if not row:
                return None
            return dict(row._mapping)

        except Exception as e:
            self.db.rollback()
            print("[ERROR] update_by_id failed:", e)
            raise RuntimeError("Database update failed") from e
    
    def upsert_record(
        self,
        model,
        rows,
        update_columns=None,
        constraint_name=None,
        conflict_columns=None,
        to_commit=False
    ):
        try:
            table = model.__table__ if hasattr(model, "__table__") else model
            print(f"upsert record in {table}")
            if isinstance(rows, dict): rows = [rows]
            stmt = insert(table).values(rows).returning(table)
            if update_columns is None:
                mapper = inspect(table)
                pk_names = {c.name for c in mapper.primary_key}
                update_columns = [
                    c.name for c in table.c
                    if c.name not in pk_names
                ]
            set_dict = {
                col: getattr(stmt.excluded, col)
                for col in update_columns
                }
            if constraint_name:
                stmt = stmt.on_conflict_do_update(
                    constraint=constraint_name,
                    set_=set_dict
                )
            else:
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_columns,
                    set_=set_dict
                )
            result = self.db.execute(stmt)
            records = [row._mapping for row in result.fetchall()]
            if to_commit:
                self.db.commit()
            if len(records) == 1 and len(rows) == 1:
                return records[0]
            return records
        except Exception as e:
            print(f"[ERROR] occured while upserting",e)
            raise RuntimeError("Database sync failed during upsert") from e 
    def get_seleted_colums(self,col_names:list,model,id):
        cols = [getattr(model, name) for name in col_names]
        stmt = (
            select(*cols)
            .where(model.id == id)
        )
        row = self.db.execute(stmt).mappings().one_or_none()
        return dict(row) if row else {}
    def delete_record(self,model,column,value):
        try:
            table = model.__table__ if hasattr(model, "__table__") else model
            col = getattr(table.c, column)
            if col:
                stmt = delete(table).where(table.col == value)
                self.db.execute(stmt)
                self.db.commit()
            return {"success":True,"msg":""}
        except Exception as e:
            return {"success":False,"msg":str(e)}
        

    def get_chapters_with_progress(self, ulp_id, resource_id):
        rows = self.db.execute(
            select(
                LearningResourceChapter,
                UserChapterProgress
            )
            .join(
                UserChapterProgress,
                UserChapterProgress.learning_resource_chapter_id == LearningResourceChapter.id
            )
            .where(
                LearningResourceChapter.learning_resource_id == resource_id,
                UserChapterProgress.user_learning_progress_id == ulp_id
            )
            .order_by(LearningResourceChapter.index)
        ).mappings().all()
        result=[map_chapter_with_progress(r) for r in rows]
        return result

def map_chapter_with_progress(row):
    chapter = getattr(row, "LearningResourceChapter", None)
    progress = getattr(row, "UserChapterProgress", None)

    if chapter is None:
        return None  # or raise ValueError("Chapter missing")
    result = chapter.to_dict()
    if progress:
        result["progress"]=progress.to_dict() 
    else:
        result["progress"] = {}

    return result


def ensure_learning_resource(db_session:db_session,id):
    chapters = db_session.get_record(LearningResourceChapter,{"learning_resource_id": id},order_col='index',order_fn=asc,first_only=False)
    if chapters:
        title=db_session.get_record(LearningResource,{"id": id},first_only=True).get("title","")
        print("fetched from DB...")
    else:
        status_code,chapters_response=get_chapters(id)
        print(f"{id= },{chapters_response = }")
        chapters_response['id']=id
        title=chapters_response.get('title',None)
        chapters=chapters_response.pop('chapters',[])
        print(f"{chapters = }")
        for chapter in chapters:
            chapter.update({"learning_resource_id":id})
            print(chapter)
        learning_resource=db_session.upsert_record(LearningResource,chapters_response,conflict_columns=['id'])
        chapters=db_session.upsert_record(LearningResourceChapter,chapters,conflict_columns=['learning_resource_id','index'])
    return title,chapters



def ensure_user_progress(db_session:db_session, user_id, resource_id):
    ulp = db_session.get_record(
        UserLearningProgress,
        {"user_id": user_id, "learning_resource_id": resource_id},
        first_only=True
    )
    title=None
    if not ulp:
        title,chapters=ensure_learning_resource(db_session,resource_id)
        ulp = db_session.upsert_record(
            UserLearningProgress,
            {
                "user_id": user_id,
                "learning_resource_id": resource_id
            },
            conflict_columns=["user_id", "learning_resource_id"]
        )

        progress_rows = [
            {
                "user_learning_progress_id": ulp["id"],
                "learning_resource_chapter_id": c["id"]
            }
            for c in chapters
        ]

        ucp=db_session.upsert_record(
            UserChapterProgress,
            progress_rows,
            conflict_columns=["user_learning_progress_id", "learning_resource_chapter_id"]
        )
    else:
        title = db_session.get_record(LearningResource,{"id": resource_id},first_only=True).get("title",None)

    return title,ulp 

    
def get_userprogress(db_session:db_session,user_id=None,filters={},sort_by='last_accessed_at',order='asc'):
    try:
        if user_id:
            filters['user_id']=user_id
        print(filters)
        user_progress= db_session.get_record(
                model=UserLearningProgress,
                filters={"user_id": user_id},
                join_table=LearningResource,
                join_on=UserLearningProgress.learning_resource_id == LearningResource.id,
                order_col=LearningResource.created_at,
                order_fn=desc,
                first_only=False
            )
        print(user_progress)
        return user_progress if user_progress else []
    except Exception as e:
        print(e)
        raise e
def get_next_chapter(db_session:db_session,ulp_id):
    # join user_chapter_progress and LearningResourceChapter , order by index , where user_learning_progress_id=ulp_id and quiz_attempted == False , watched == False
    try:
        filters={
            "user_learning_progress_id":ulp_id,
            "quiz_attempted":False,
            "watched":False
        }
        stmt = (
            select(LearningResourceChapter, UserChapterProgress)
            .join(
                UserChapterProgress,
                UserChapterProgress.learning_resource_chapter_id
                == LearningResourceChapter.id
            )
            .where(
                UserChapterProgress.user_learning_progress_id == ulp_id,
                UserChapterProgress.watched.is_(False),
                UserChapterProgress.quiz_attempted.is_(False),
            )
            .order_by(asc(LearningResourceChapter.index))
            .limit(1)
        )

        row = db_session.execute_stmt(stmt, first=True)
        if row:
            chapter, progress = row
            return chapter.to_dict() , progress.to_dict()
        return {},{}
    except Exception:
        raise

def set_userChapter_progress(db_session:db_session,user_id,chapter_progress_id,payload):
    attempt_count=db_session.get_seleted_colums(["attempts_count"],UserChapterProgress,chapter_progress_id).get("attempts_count",0)
    print(type(attempt_count))
    print(attempt_count)
    payload["attempts_count"]+=attempt_count
    user_chapter_prg=db_session.update_by_id(
        UserChapterProgress,
        chapter_progress_id,
        payload
        )
    if user_chapter_prg:
        return user_chapter_prg
    return None

def mark_chapter_watched(db_session:db_session, ucp_id: int):
    try:
        if not ucp_id : return
        print("marking chapter as completed")
        db_session.update_by_id(UserChapterProgress,ucp_id,payload={
            "watched":True
        })
        return True
    except Exception as e:
        print("[ERROR]...",{e})
        raise e
    

def fetch_learning_resource(db_session,id:str):
    filters={
        "id":id
    }
    resource=db_session.get_record(LearningResource,filters,first_only=True)
    return resource

def fetch_resource_chapters(db_session:db_session,resource_id):
    filters={
        "learning_resource_id":str(resource_id)
    }
    chapters=db_session.get_record(LearningResourceChapter,filters,order_col='index',order_fn=asc,first_only=False)
    return chapters

def update_trancripts(db_session:db_session,chapters):
    try:
        for chapter in chapters:
            print(chapter['id'],len(chapter["transcript"]))
            db_session.update_by_id(LearningResourceChapter,chapter['id'], {"transcript": chapter["transcript"]},commit=True)
        return True
    except Exception:
        raise

def update_dailybite(db_session: db_session, id:int, payload):
    try:
        db_session.update_by_id(
            UserLearningProgress,
            id,
            payload=payload,
            commit=True
        )
        return True
    except Exception:
        raise

def fetch_progress(db_session: db_session,ulp_id:int):
    try:
        filters={
            "id":ulp_id
        }
        resource=db_session.get_record(UserLearningProgress,filters,first_only=True)
        return resource
    except Exception:
        raise

