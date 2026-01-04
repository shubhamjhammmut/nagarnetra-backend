from fastapi import FastAPI
from routes.detect import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NagarNetra Mock AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"status": "Mock AI Backend Running"}
