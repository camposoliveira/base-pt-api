# main.py
# API simples para pesquisar datasets relacionados ao Portal BASE em dados.gov.pt
# Usa FastAPI para expor endpoints

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import requests
from urllib.parse import urlencode

app = FastAPI(
    title="BASE-PT API",
    description="Pesquisa datasets de contratação pública no dados.gov.pt",
    version="1.0.0"
)

# URL da API CKAN do dados.gov.pt
CKAN_BASE = "https://dados.gov.pt/api/3/action"


# Modelo de resposta para cada item
class SearchItem(BaseModel):
    title: str
    organization: Optional[str] = None
    notes: Optional[str] = None
    metadata_created: Optional[str] = None
    url: Optional[str] = None
    source: str = "dados.gov.pt"


class SearchResponse(BaseModel):
    query: str
    count: int
    results: List[SearchItem]


# Função interna para consultar CKAN
def _ckan_package_search(q: str, rows: int = 10, start: int = 0):
    params = {
        "q": q,
        "rows": rows,
        "start": start,
        "sort": "score desc, metadata_modified desc"
    }
    url = f"{CKAN_BASE}/package_search?{urlencode(params)}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError("Erro na resposta do CKAN")
    return data["result"]


# Endpoint principal /search
@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., description="Termo de pesquisa, ex.: Portal BASE contratos públicos"),
    rows: int = 10,
    start: int = 0
):
    res = _ckan_package_search(q=q, rows=rows, start=start)
    items = []
    for pkg in res.get("results", []):
        items.append(SearchItem(
            title=pkg.get("title") or pkg.get("name") or "Sem título",
            organization=(pkg.get("organization") or {}).get("title"),
            notes=pkg.get("notes"),
            metadata_created=pkg.get("metadata_created"),
            url=f"https://dados.gov.pt/pt/datasets/{pkg.get('name')}" if pkg.get("name") else None
        ))
    return JSONResponse(SearchResponse(query=q, count=res.get("count", 0), results=items).dict())
