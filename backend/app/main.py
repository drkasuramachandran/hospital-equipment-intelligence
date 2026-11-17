import os
from datetime import date, datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from jose import jwt, JWTError
from passlib.context import CryptContext
from .database import Base, engine, get_db
from . import models, schemas

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Hospital Equipment Readiness API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173","http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET = os.getenv("JWT_SECRET", "development-only-change-this-secret-before-deployment")
ALGORITHM = "HS256"

def seed(db):
    if not db.scalar(select(models.User).where(models.User.email == "admin@hospital.local")):
        db.add(models.User(email="admin@hospital.local", password_hash=pwd.hash("Hospital@123"), name="Hospital Administrator", role="admin"))
    if db.scalar(select(models.Equipment.id)) is None:
        samples = [
            models.Equipment(asset_code="ICU-MON-001", name="Multiparameter Patient Monitor", category="Patient Monitoring", manufacturer="Mindray", model="uMEC 10", department="ICU", location="ICU - Bed 01", status="Available", risk_level="High", next_pm_date=date.today()+timedelta(days=12), next_calibration_date=date.today()+timedelta(days=40)),
            models.Equipment(asset_code="RAD-XR-002", name="Digital X-ray System", category="Imaging", manufacturer="Carestream", model="DRX", department="Radiology", location="Radiology Room 1", status="Under Maintenance", risk_level="High", next_pm_date=date.today()-timedelta(days=4), next_calibration_date=date.today()+timedelta(days=70)),
            models.Equipment(asset_code="OT-VENT-003", name="Anaesthesia Workstation", category="Life Support", manufacturer="Dräger", model="Fabius", department="Operation Theatre", location="OT 2", status="Available", risk_level="Critical", next_pm_date=date.today()+timedelta(days=25), next_calibration_date=date.today()+timedelta(days=15)),
        ]
        db.add_all(samples)
    db.commit()

@app.on_event("startup")
def startup():
    db = next(get_db())
    try: seed(db)
    finally: db.close()

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    try:
        payload = jwt.decode(authorization[7:], SECRET, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(401, "Invalid or expired session")
    user = db.get(models.User, user_id)
    if not user: raise HTTPException(401, "User not found")
    return user

@app.get("/api/health")
def health(): return {"status":"ok","service":"hospital-equipment-readiness-api"}

@app.post("/api/auth/login")
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == data.email.lower()))
    if not user or not pwd.verify(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    token = jwt.encode({"sub":str(user.id),"exp":datetime.utcnow()+timedelta(hours=8)}, SECRET, algorithm=ALGORITHM)
    return {"access_token":token,"token_type":"bearer","user":{"name":user.name,"email":user.email,"role":user.role}}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(current_user)):
    total = db.scalar(select(func.count(models.Equipment.id))) or 0
    available = db.scalar(select(func.count(models.Equipment.id)).where(models.Equipment.status=="Available")) or 0
    down = db.scalar(select(func.count(models.Equipment.id)).where(models.Equipment.status=="Out of Service")) or 0
    overdue_pm = db.scalar(select(func.count(models.Equipment.id)).where(models.Equipment.next_pm_date < date.today())) or 0
    open_orders = db.scalar(select(func.count(models.WorkOrder.id)).where(models.WorkOrder.status!="Closed")) or 0
    due_cal = db.scalar(select(func.count(models.Equipment.id)).where(models.Equipment.next_calibration_date <= date.today()+timedelta(days=30))) or 0
    return {"total_equipment":total,"available":available,"out_of_service":down,"overdue_pm":overdue_pm,"open_work_orders":open_orders,"calibration_due_30d":due_cal}

@app.get("/api/equipment", response_model=list[schemas.EquipmentOut])
def list_equipment(q: str="", department: str="", db: Session=Depends(get_db), user=Depends(current_user)):
    stmt=select(models.Equipment).order_by(models.Equipment.created_at.desc())
    if q: stmt=stmt.where((models.Equipment.name.ilike(f"%{q}%"))|(models.Equipment.asset_code.ilike(f"%{q}%")))
    if department: stmt=stmt.where(models.Equipment.department==department)
    return list(db.scalars(stmt))

@app.post("/api/equipment", response_model=schemas.EquipmentOut)
def add_equipment(data: schemas.EquipmentIn, db: Session=Depends(get_db), user=Depends(current_user)):
    if db.scalar(select(models.Equipment).where(models.Equipment.asset_code==data.asset_code)):
        raise HTTPException(409,"Asset code already exists")
    item=models.Equipment(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@app.patch("/api/equipment/{equipment_id}/status")
def update_status(equipment_id:int, status:str, db:Session=Depends(get_db), user=Depends(current_user)):
    item=db.get(models.Equipment,equipment_id)
    if not item: raise HTTPException(404,"Equipment not found")
    if status not in ["Available","Under Maintenance","Out of Service","Retired"]: raise HTTPException(400,"Invalid status")
    item.status=status; db.commit(); return {"ok":True,"status":status}

@app.get("/api/work-orders", response_model=list[schemas.WorkOrderOut])
def work_orders(db:Session=Depends(get_db), user=Depends(current_user)):
    return list(db.scalars(select(models.WorkOrder).order_by(models.WorkOrder.created_at.desc())))

@app.post("/api/work-orders", response_model=schemas.WorkOrderOut)
def create_work_order(data:schemas.WorkOrderIn, db:Session=Depends(get_db), user=Depends(current_user)):
    if data.equipment_id and not db.get(models.Equipment,data.equipment_id): raise HTTPException(404,"Equipment not found")
    item=models.WorkOrder(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@app.patch("/api/work-orders/{work_order_id}/close")
def close_work_order(work_order_id:int, db:Session=Depends(get_db), user=Depends(current_user)):
    item=db.get(models.WorkOrder,work_order_id)
    if not item: raise HTTPException(404,"Work order not found")
    item.status="Closed"; db.commit(); return {"ok":True}

@app.get("/api/maintenance")
def maintenance(db:Session=Depends(get_db), user=Depends(current_user)):
    return [{"id":t.id,"equipment_id":t.equipment_id,"task_type":t.task_type,"due_date":str(t.due_date),"assigned_to":t.assigned_to,"status":t.status} for t in db.scalars(select(models.MaintenanceTask).order_by(models.MaintenanceTask.due_date))]

@app.post("/api/maintenance")
def add_maintenance(data:schemas.TaskIn, db:Session=Depends(get_db), user=Depends(current_user)):
    if not db.get(models.Equipment,data.equipment_id): raise HTTPException(404,"Equipment not found")
    task=models.MaintenanceTask(**data.model_dump()); db.add(task); db.commit(); db.refresh(task); return {"id":task.id,"status":task.status}

@app.get("/api/inspections")
def inspections(db:Session=Depends(get_db), user=Depends(current_user)):
    return [{"id":i.id,"equipment_id":i.equipment_id,"inspection_date":str(i.inspection_date),"outcome":i.outcome,"findings":i.findings,"inspector":i.inspector} for i in db.scalars(select(models.SafetyInspection).order_by(models.SafetyInspection.inspection_date.desc()))]

@app.post("/api/inspections")
def add_inspection(data:schemas.InspectionIn, db:Session=Depends(get_db), user=Depends(current_user)):
    if not db.get(models.Equipment,data.equipment_id): raise HTTPException(404,"Equipment not found")
    item=models.SafetyInspection(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return {"id":item.id}
