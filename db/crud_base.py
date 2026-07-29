from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session
from db.database import SessionLocal

ModelType = TypeVar("ModelType")


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

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
            return session.query(self.model).filter(self.model.id == id).first()
        finally:
            session.close()

    def get_all(self) -> List[ModelType]:
        session: Session = SessionLocal()
        try:
            return session.query(self.model).all()
        finally:
            session.close()

    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        session: Session = SessionLocal()
        try:
            obj = session.query(self.model).filter(self.model.id == id).first()
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
            obj = session.query(self.model).filter(self.model.id == id).first()
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        finally:
            session.close()