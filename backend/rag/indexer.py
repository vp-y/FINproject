from rag.loader import load_document_pages
from rag.splitter import split_text


def index_document(path, document_name, company, document_type, year, section=None):

    pages = load_document_pages(path)

    indexed_chunks = []
    chunk_counter = 0

    for page in pages:

        page_chunks = split_text(page["text"])

        for chunk_text in page_chunks:

            chunk_counter += 1

            chunk_metadata = {
                "chunk_id": f"{document_name}_p{page['page']}_c{chunk_counter}",
                "document_name": document_name,
                "page_number": page["page"],
                "company": company,
                "document_type": document_type,
                "year": year
            }

            if section:
                chunk_metadata["section"] = section

            indexed_chunks.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })

    print(
        "Chunks:",
        len(indexed_chunks)
    )

    return indexed_chunks
