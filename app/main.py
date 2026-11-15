from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.routes import router as video_router
from fastapi.responses import FileResponse



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


# --------------------------------------------------
# GOOGLE SEO - ROBOTS.TXT
# --------------------------------------------------

@app.get("/robots.txt", include_in_schema=False)
def robots_txt():
    return FileResponse(
        "app/static/robots.txt",
        media_type="text/plain"
    )


# --------------------------------------------------
# GOOGLE SEO - SITEMAP.XML
# --------------------------------------------------

@app.get("/sitemap.xml", include_in_schema=False)
def sitemap_xml():
    return FileResponse(
        "app/static/sitemap.xml",
        media_type="application/xml"
    )


app.include_router(video_router, prefix="/api/video", tags=["video"])