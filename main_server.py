from fastapi import FastAPI, Depends, Body, Request, Response, HTTPException
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable, OrderTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from pydantic import BaseModel
import os
import uvicorn

main = FastAPI()

main.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://red-ctcfbq2j1k6c73ffbtsg:6379")
redis = Redis.from_url(REDIS_URL, decode_responses=True)

class UserInfo(BaseModel):
    order_id: int

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

# 로그인 상태 확인
@main.get("/check_login/")
async def check_login(request: Request):
    # 쿠키에서 세션 ID 가져오기
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session found")

    # Redis에서 세션 데이터 가져오기
    session_data = await redis.get(session_id)
    if not session_data:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    return {"success": True, "session_id": session_id, "session_data": session_data}

# 로그아웃 처리
@main.post("/logout/")
async def logout(request: Request, response: Response):
    # 쿠키에서 세션 ID 가져오기
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")

    # Redis에서 세션 삭제
    result = await redis.delete(session_id)
    if result == 0:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    # 쿠키에서 세션 ID 삭제
    response.delete_cookie("session_id")

    return {"success": True, "message": "Logged out successfully"}

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

#is_completed가 false인 order들의 order_id를 리스트로 반환
@main.get("/order/active_order_ids/{user_id}")
async def get_active_order_ids(user_id: str, db: Session = Depends(get_db)):
    order_ids = db.query(OrderTable.order_id).filter(OrderTable.user_id == user_id, OrderTable.is_completed == False).all()
    
    return {"order_ids": [order_id[0] for order_id in order_ids]}

# 총 수량 반환
@main.get("/total_count/{user_id}")
async def read_total_count(user_id: str, db: Session = Depends(get_db)):
    orders = db.query(
                        OrderTable.quantity,
                        OrderTable.is_completed,
                        UserTable.user_id
                    ).join(UserTable, UserTable.user_id == OrderTable.user_id).filter(OrderTable.user_id == user_id, OrderTable.is_completed == False).all()
    
    counts = [row[0] for row in orders] 
    total = sum(counts)
    
    return total

#장바구니 -버튼 처리
@main.put("/order/decrease/")
async def decrease_order_quantity(request: UserInfo, db: Session = Depends(get_db)):
    order = db.query(OrderTable).filter(OrderTable.order_id == request.order_id, OrderTable.is_completed == False).first()
    
    if order:
        order.quantity -= 1
        
        if order.quantity <= 0:
            db.delete(order)
    
        db.commit()
        db.refresh(order)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)