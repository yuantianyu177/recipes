"""MeiliSearch integration service for recipe indexing and search."""
import meilisearch
from app.core.config import settings

_client: meilisearch.Client | None = None
INDEX_NAME = "recipes"


def get_meili_client() -> meilisearch.Client:
    global _client
    if _client is None:
        _client = meilisearch.Client(settings.MEILI_HOST, settings.MEILI_MASTER_KEY)
    return _client


def setup_index():
    """Configure MeiliSearch index settings."""
    client = get_meili_client()
    index = client.index(INDEX_NAME)
    # Searchable attributes by priority: name > main ingredients > tags
    index.update_searchable_attributes(["name", "main_ingredients", "tags"])
    # Filterable attributes for tag filtering
    index.update_filterable_attributes(["tags"])
    # Sortable attributes
    index.update_sortable_attributes(["name"])


def index_recipe(recipe_id: int, name: str, tags: list[str], main_ingredients: list[str]):
    """Add or update a recipe in the search index."""
    client = get_meili_client()
    index = client.index(INDEX_NAME)
    doc = {
        "id": recipe_id,
        "name": name,
        "tags": tags,
        "main_ingredients": main_ingredients,
    }
    index.add_documents([doc])


def remove_recipe(recipe_id: int):
    """Remove a recipe from the search index."""
    client = get_meili_client()
    index = client.index(INDEX_NAME)
    index.delete_document(recipe_id)


def search_recipes(query: str, tag_filter: str | None = None, limit: int = 20, offset: int = 0) -> dict:
    """Search recipes via MeiliSearch.

    Args:
        query: Search query string
        tag_filter: Optional MeiliSearch filter string, e.g. 'tags = "川菜"'
        limit: Max results to return
        offset: Offset for pagination

    Returns:
        MeiliSearch search result dict with 'hits', 'estimatedTotalHits', etc.
    """
    client = get_meili_client()
    index = client.index(INDEX_NAME)
    params = {"limit": limit, "offset": offset}
    if tag_filter:
        params["filter"] = tag_filter
    return index.search(query, params)


def get_synonyms() -> dict[str, list[str]]:
    """Get current synonym groups from MeiliSearch."""
    client = get_meili_client()
    index = client.index(INDEX_NAME)
    return index.get_synonyms()


def update_synonyms(synonyms: dict[str, list[str]]):
    """Update synonym groups in MeiliSearch with bidirectional expansion.

    Input: {"番茄": ["西红柿", "洋柿子"]}
    Expanded: each word in the group maps to all others.
    """
    # Build bidirectional synonym map
    expanded: dict[str, set[str]] = {}
    for key, vals in synonyms.items():
        group = {key.strip()} | {v.strip() for v in vals if v.strip()}
        for word in group:
            if word not in expanded:
                expanded[word] = set()
            expanded[word].update(group - {word})

    final = {k: sorted(v) for k, v in expanded.items() if v}
    client = get_meili_client()
    index = client.index(INDEX_NAME)
    index.update_synonyms(final)
