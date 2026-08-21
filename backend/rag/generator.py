from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client()

MODEL = "gemini-3.6-flash"


def generate_answer(
    query,
    context
):

    prompt = f"""
Answer using only this context:
{context}

Question:
{query}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text


def generate_answer_with_sources(
    query,
    chunks
):
    """
    chunks: list of {"text": ..., "metadata": {...}} — e.g. retrieved
    from Qdrant, where metadata carries document_name/page_number as
    set up in rag/indexer.py.
    """

    context = "\n\n".join(
        chunk["text"] for chunk in chunks
    )

    answer = generate_answer(
        query,
        context
    )

    sources = []
    seen = set()

    for chunk in chunks:

        metadata = chunk["metadata"]
        key = (metadata.get("document_name"), metadata.get("page_number"))

        if key in seen:
            continue

        seen.add(key)

        sources.append({
            "document": metadata.get("document_name"),
            "page": metadata.get("page_number")
        })

    return {
        "answer": answer,
        "sources": sources
    }
