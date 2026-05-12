from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from Routes.umlRoutes import router as uml_router


# FASTAPI APP
app = FastAPI()

# ====================================
# CORS
# ====================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================================
# ROUTES
# ====================================

app.include_router(uml_router)

# ====================================
# ROOT ENDPOINT
# ====================================

@app.get("/")
def home():

    return {
        "message": "AI UML Generator Backend Running"
    }


# ====================================
# RUN SERVER
# ====================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )