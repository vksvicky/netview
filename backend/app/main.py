from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from .routers import devices, interfaces, topology, alerts, metrics as metrics_api
from .scheduler import start_scheduler
from .metrics import registry, http_requests_total
from .db import initialize_database


app = FastAPI(title="NetView", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


"""Metrics are centrally declared in app.metrics"""


@app.middleware("http")
async def metrics_middleware(request, call_next):
    response = await call_next(request)
    try:
        http_requests_total.labels(
            method=request.method, path=request.url.path, status=str(response.status_code)
        ).inc()
    except Exception:
        pass
    return response


@app.get("/metrics")
def metrics():
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(interfaces.router, prefix="/interfaces", tags=["interfaces"])
app.include_router(topology.router, prefix="/topology", tags=["topology"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(metrics_api.router, prefix="/metrics", tags=["metrics-json"])


@app.on_event("startup")
async def on_startup():
    initialize_database()
    start_scheduler()


