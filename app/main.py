from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.routes import router as video_router



app = FastAPI(
    title="MediaFetch",
    description="A responsive media utility",
    version="1.0.0"

)

# Serve CSS and JavaScript
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

# Configure HTML templates
templates = Jinja2Templates(directory="app/templates")


#Homepage
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
        
    )

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "MediaFetch"
    }

app.include_router(video_router, prefix="/api/video", tags=["video"])