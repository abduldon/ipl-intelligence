from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import os

from backend.routes import players, teams, auction, export
from backend.routes import auth_routes, squad_routes

app = FastAPI(
    title="IPL Intelligence Platform",
    description="Decision support system for IPL teams, analysts and commentators",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(squad_routes.router)
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(auction.router)
app.include_router(export.router)

frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/login")
def login_page():
    return FileResponse(os.path.join(frontend_path, "login.html"))

@app.get("/login.html")
def login_html_redirect():
    return RedirectResponse(url="/login")

@app.get("/index.html")
def index_html():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/manifest.json")
def manifest():
    return FileResponse(os.path.join(frontend_path, "manifest.json"))

@app.get("/sw.js")
def service_worker():
    return FileResponse(os.path.join(frontend_path, "sw.js"),
                       media_type="application/javascript")

@app.get("/{full_path:path}")
def catch_all(full_path: str):
    return FileResponse(os.path.join(frontend_path, "index.html"))