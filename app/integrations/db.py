
from app.models.learning import LearningResource , LearningResourceChapter , UserChapterProgress , UserLearningProgress
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session 
from sqlalchemy import delete ,select , asc , desc
from sqlalchemy.dialects.postgresql import insert 
from sqlalchemy import update

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
                    if col in table.c:
                        stmt = stmt.where(getattr(table.c, col) == value)

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
            valid_columns = set(table.c.keys())
            update_payload = {
                k: v for k, v in payload.items()
                if k in valid_columns and k not in pk_names
            }
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

        except Exception :
            self.db.rollback()
            print("[ERROR] update_by_id failed:")
            raise 
    
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
        except Exception :
            print(f"[ERROR] occured while upserting")
            raise 
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
        result=[self.map_chapter_with_progress(r) for r in rows]
        return result
    def map_chapter_with_progress(self,row):
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