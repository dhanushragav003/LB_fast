from fastapi import FastAPI
from app.routes import quiz , users , dailybite
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from jinja2_markdown import MarkdownExtension


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
templates.env.add_extension(MarkdownExtension)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(quiz.route)
app.include_router(users.route)
app.include_router(dailybite.route)


@app.get('/api/health/')
def health():
    return {"msg":"fast api is up","status":"OK"}
