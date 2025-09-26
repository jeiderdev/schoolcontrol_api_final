from fastapi import FastAPI, Request
from database import engine, Base
from models import __all__
from routes import routers

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.middleware("http")
async def log_url_middleware(request: Request, call_next):
    print(f"➡️ {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"⬅️ {response.status_code} {request.url.path}")
    return response


# Incluir todas las rutas
for r in routers:
    app.include_router(r)

@app.get("/")
def root():
    return {"message": "Hola Escuela 🚀"}

def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    import uvicorn
    local_ip = get_local_ip()
    print(f"🚀 Backend corriendo en: http://{local_ip}:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
