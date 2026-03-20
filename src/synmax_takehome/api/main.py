from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SynMax take-home",
        description="NM well data API (Part 2 wires routers here).",
        lifespan=_lifespan,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Part 2:
    from synmax_takehome.api.routers import spatial, wells

    app.include_router(wells.router)
    app.include_router(spatial.router)

    return app


app = create_app()
