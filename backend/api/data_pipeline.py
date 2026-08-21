from fastapi import APIRouter

from data_pipeline.pipeline import process_portfolio

router = APIRouter(
    prefix="/data",
    tags=["Data Pipeline"]
)


@router.post("/sync")
def sync_portfolio(
    data: dict
):

    docs = process_portfolio(
        data["holdings"]
    )

    return {

        "status": "completed",

        "documents": docs

    }
