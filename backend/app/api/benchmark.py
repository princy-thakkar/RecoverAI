from fastapi import APIRouter, HTTPException, Query

from app.recovery.benchmark import RecoveryBenchmark

router = APIRouter(
    prefix="/api/benchmark",
    tags=["benchmark"],
)

benchmark = RecoveryBenchmark()


@router.get("")
async def run_benchmark(
    size: int = Query(
        default=250,
        ge=1,
        le=5000,
    ),
    seed: int = Query(
        default=2026,
    ),
):
    try:
        return benchmark.run(
            batch_size=size,
            seed=seed,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc