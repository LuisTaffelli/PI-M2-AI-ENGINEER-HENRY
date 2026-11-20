def context_items(selected):
    return [{"chunk_id": item.chunk.chunk_id, "content": item.chunk.content} for item in selected]
