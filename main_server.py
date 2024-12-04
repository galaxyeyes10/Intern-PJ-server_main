from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable
from db import session
from fastapi.middleware.cors import CORSMiddleware

main = FastAPI()

main.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

#유저 아이디로 닉네임 반환
@main.get("/username/{user_id}")
async def read_username(user_id: str, db: Session = Depends(get_db)):
    reviewer = db.query(ReviewTable).join(UserTable).filter(ReviewTable.user_id == user_id).first()
    
    return reviewer.user.username

#가게 아이디로 가게 사진 반환
@main.get("/store_img/{store_id}")
async def read_store_img(store_id: str, db: Session = Depends(get_db)):
    store = db.query(StoreTable).filter(StoreTable.store_id == store_id).first()

    return store.store_img

#가게 아이디로 가게 이름 반환
@main.get("/store_name/{store_id}")
async def read_store_name(store_id: str, db: Session = Depends(get_db)):
    store = db.query(StoreTable).filter(StoreTable.store_id == store_id).first()

    return store.store_name

#플러스 버튼 클릭 시 데이터베이스 상 수량 증가
#마이너스 버튼 클릭 시 데이터베이스 상 수량 감소