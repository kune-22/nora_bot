from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from db.database import SessionLocal

ModelType = TypeVar("ModelType")


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def _primary_key_column(self):
        return inspect(self.model).primary_key[0]

    def create(self, **kwargs) -> ModelType:
        session: Session = SessionLocal()
        try:
            obj = self.model(**kwargs)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
        finally:
            session.close()

    def get(self, id: int) -> Optional[ModelType]:
        session: Session = SessionLocal()
        try:
            return session.query(self.model).filter(self._primary_key_column() == id).first()
        finally:
            session.close()

    def get_all(self) -> List[ModelType]:
        session: Session = SessionLocal()
        try:
            return session.query(self.model).all()
        finally:
            session.close()

    def get_all_by(self, **filters) -> List[ModelType]:
        """指定したカラム値に一致するレコードをすべて取得する。"""
        session: Session = SessionLocal()
        try:
            query = session.query(self.model)
            for column_name, value in filters.items():
                query = query.filter(getattr(self.model, column_name) == value)
            return query.all()
        finally:
            session.close()

    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        session: Session = SessionLocal()
        try:
            obj = session.query(self.model).filter(self._primary_key_column() == id).first()
            if obj:
                for key, value in kwargs.items():
                    setattr(obj, key, value)
                session.commit()
                session.refresh(obj)
            return obj
        finally:
            session.close()

    def delete(self, id: int) -> bool:
        session: Session = SessionLocal()
        try:
            obj = session.query(self.model).filter(self._primary_key_column() == id).first()
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        finally:
            session.close()
