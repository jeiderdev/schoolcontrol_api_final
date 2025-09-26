from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, UserRole
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config import settings
from routes.dtos import CreateUserDto, LoginDto, TokenDto, UpdateUserDto, UserDto

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.post("/login", response_model=TokenDto)
async def login(login_data: LoginDto, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password):
        print("Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    
    if not user.active:
        print("Inactive account")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta no activada",
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user 
    }

@router.post("/register", response_model=UserDto)
async def register(user_data: CreateUserDto, db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    if curr_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permiso para registrar usuarios")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    if db.query(User).filter(User.idnumber == user_data.idnumber).first():
        raise HTTPException(status_code=400, detail="Número de identificación ya registrado")
    
    hashed_password = get_password_hash(user_data.password)
    if user_data.photo != None and user_data.photo.strip() == "":
        user_data.photo = None
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        idnumber=user_data.idnumber,
        password=hashed_password,
        role=user_data.role,
        age=user_data.age,
        photo=user_data.photo,
        active=user_data.active,
    )
    try:
        print("Adding user to database")
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {str(e)}")
    return db_user

@router.get("/me", response_model=UserDto)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserDto)
async def update_user(user_data: UpdateUserDto, db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == curr_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if curr_user.role != UserRole.ADMIN and curr_user.id != user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este usuario")
    
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.age is not None:
        user.age = user_data.age
    if user_data.password is not None:
        user.password = get_password_hash(user_data.password)
    if user_data.photo is not None:
        user.photo = user_data.photo
    if user_data.active is not None:
        user.active = user_data.active
    
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")
    return user

@router.put("/{user_id}", response_model=UserDto)
async def update_user(user_id: int, user_data: UpdateUserDto, db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if curr_user.role != UserRole.ADMIN and curr_user.id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este usuario")
    
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.age is not None:
        user.age = user_data.age
    if user_data.password is not None:
        user.password = get_password_hash(user_data.password)
    if user_data.photo is not None:
        user.photo = user_data.photo
    if user_data.active is not None:
        user.active = user_data.active
    
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")
    return user

@router.get("/admins", response_model=list[UserDto])
def list_admins(db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    if curr_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver los administradores")
    return db.query(User).filter(User.role == UserRole.ADMIN).all()

@router.get("/teachers", response_model=list[UserDto])
def list_teachers(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == UserRole.TEACHER).all()

@router.get("/students", response_model=list[UserDto])
def list_students(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == UserRole.STUDENT).all()