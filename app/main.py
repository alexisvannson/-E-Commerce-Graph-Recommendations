from fastapi import FastAPI


app = FastAPI(title="E-Commerce Graph Recommendations")


@app.get("/")
def read_root() -> dict:
    return {"status": "ok"}


@app.get("/health")
def health() -> dict:
    return {"ok": True}


