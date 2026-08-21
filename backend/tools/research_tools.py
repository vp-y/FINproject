from rag.retriever import retrieve


def search_financial_documents(
    query: str,
    company: str | None = None,
) -> dict:
    """
    Search the internal financial document knowledge base.

    Use this tool for questions about company annual reports,
    risk factors, financial statements, business operations,
    or information contained in downloaded documents.

    Args:
        query: Search query.
        company: Optional ticker or company filter.

    Returns:
        Relevant document chunks and metadata.
    """

    results = retrieve(
        query=query,
        company=company,
    )

    return {
        "query": query,
        "company": company,
        "results": results,
    }
