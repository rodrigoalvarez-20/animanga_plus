from starlette.responses import JSONResponse
from fastapi import FastAPI
import uvicorn

from routes.anime import router as AnimeRouter

app = FastAPI()

@app.get("/api/v1")
def main_route():
    return JSONResponse({ "message": "Ok" }, 200)

app.include_router(AnimeRouter)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port="8000", debug=True)