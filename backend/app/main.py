from fastapi import FastAPI
from app.api.v1.routers import app as api_v1

app = FastAPI(title="romulus")
app.mount("/api/v1", api_v1)

def main():
    pass

if __name__ == "__main__":
    main()