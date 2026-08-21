from fastapi import APIRouter
from rag.retriever import retrieve


router = APIRouter(
    prefix="/rag",
    tags=["RAG"]
)


@router.get("/search")
def search(
    query: str
):

    results = retrieve(
        query
    )

    return {

        "query": query,

        "results": results

    }
