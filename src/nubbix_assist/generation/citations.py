from .contracts.response import Citation


def resolve(ids, selected):
    context = {item.chunk.chunk_id: item for item in selected}
    return [Citation(key, context[key].chunk.source, context[key].chunk.content, context[key].score)
            for key in ids]
