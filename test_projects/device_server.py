from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./device_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="设备管理被测系统", version="1.0")

ALLOW_STATUS = ["online", "offline", "fault"]


class DeviceDB(Base):
    __tablename__ = "devices"
    device_id = Column(String, primary_key=True, index=True)
    device_name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    status = Column(String, default="offline", nullable=False)
    create_time = Column(DateTime, default=datetime.now, nullable=False)


Base.metadata.create_all(bind=engine)


class DeviceRegisterReq(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    device_name: str = Field(..., min_length=1, max_length=128)
    device_type: str = Field(..., min_length=1, max_length=64)


class DeviceStatusReq(BaseModel):
    status: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/device/register", summary="注册设备")
def register_device(req: DeviceRegisterReq, db: Session = Depends(get_db)):
    exist_dev = db.query(DeviceDB).filter(DeviceDB.device_id == req.device_id).first()
    if exist_dev:
        raise HTTPException(status_code=400, detail="设备ID已存在，重复注册")
    dev = DeviceDB(
        device_id=req.device_id,
        device_name=req.device_name,
        device_type=req.device_type,
        status="offline",
    )
    db.add(dev)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="注册失败")
    return {"code": 0, "msg": "注册成功", "data": {"device_id": req.device_id}}


@app.get("/device/list", summary="获取全部设备列表")
def list_devices(db: Session = Depends(get_db)):
    dev_list = db.query(DeviceDB).all()
    result = []
    for item in dev_list:
        result.append({
            "device_id": item.device_id,
            "device_name": item.device_name,
            "device_type": item.device_type,
            "status": item.status,
            "create_time": item.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return {"code": 0, "data": result}


@app.get("/device/{device_id}", summary="查询单个设备")
def get_device(device_id: str, db: Session = Depends(get_db)):
    dev = db.query(DeviceDB).filter(DeviceDB.device_id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    return {
        "code": 0,
        "data": {
            "device_id": dev.device_id,
            "device_name": dev.device_name,
            "device_type": dev.device_type,
            "status": dev.status,
            "create_time": dev.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        },
    }


@app.put("/device/{device_id}/status", summary="修改设备状态")
def update_device_status(device_id: str, req: DeviceStatusReq, db: Session = Depends(get_db)):
    if req.status not in ALLOW_STATUS:
        raise HTTPException(status_code=400, detail=f"非法状态，允许状态：{ALLOW_STATUS}")
    dev = db.query(DeviceDB).filter(DeviceDB.device_id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    dev.status = req.status
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="状态更新失败")
    return {"code": 0, "msg": "状态更新成功"}


@app.delete("/device/{device_id}", summary="删除设备")
def delete_device(device_id: str, db: Session = Depends(get_db)):
    dev = db.query(DeviceDB).filter(DeviceDB.device_id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    db.delete(dev)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="删除失败")
    return {"code": 0, "msg": "删除成功"}


@app.get("/mock/server500", summary="模拟服务500错误")
def mock_server_500():
    raise HTTPException(status_code=500, detail="模拟服务器内部错误")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
