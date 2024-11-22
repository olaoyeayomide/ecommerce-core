from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends
from typing import Annotated
from sqlalchemy.orm import Session

# SQLALCHEMY_DATABASE_URL = (
#     "postgresql://postgres:WorkTheWord1@localhost:5432/AuthGuardDatabase"
# )

# engine = create_engine(SQLALCHEMY_DATABASE_URL)

sqlite_file_name = "user.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

Base.metadata.create_all(engine)
