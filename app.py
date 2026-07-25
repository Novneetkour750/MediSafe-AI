from routes.search import router as search_router
from routes.countries import router as countries_router
from routes.medicines import router as medicines_router
from routes.upload import router as upload_router
from routes.chat import router as chat_router
from routes.stats import router as stats_router
from routes.health import router as health_router
from fastapi import FastAPI
from services.csv_services import get_dataframe

app = FastAPI()
app.include_router(search_router)
app.include_router(countries_router)
app.include_router(medicines_router)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(stats_router)
app.include_router(health_router)
df = get_dataframe()

@app.get("/")
def home():
    return {"message": "Welcome to MediSafe AI Backend"}


