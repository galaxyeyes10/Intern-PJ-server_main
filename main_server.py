from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable, OrderTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import uvicorn

main = FastAPI()

main.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

main.add_middleware(SessionMiddleware, secret_key="your-secret-key")

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

#로그인 상태 확인
@main.get("/check_login/")
async def check_login(request: Request):
    # 세션에서 사용자 정보 확인
    if "user_id" not in request.session:
        return False
    
    return {"message": f"Logged in as {request.session['username']}"}

# 로그아웃 처리
@main.post("/logout/")
async def logout(request: Request):
    # 세션에서 사용자 정보 삭제
    request.session.clear()
    return {"message": "Logged out successfully"}

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

#마이너스 버튼 클릭 시 데이터베이스 상 수량 감소
@main.put("/order/decrease/{order_id}")
async def decrease_order_quantity(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderTable).filter(OrderTable.order_id == order_id, OrderTable.is_completed == False).first()
    
    if order:
        order.quantity -= 1
        
        if order.quantity <= 0:
            db.delete(order)
    
        db.commit()
        db.refresh(order)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)