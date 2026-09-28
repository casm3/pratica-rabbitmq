import os

from fastapi import FastAPI, HTTPException, Query
from zeep import Client

app = FastAPI(title="Adapter de estoque")


@app.get("/estoques/{sku}")
def consultar_estoque(sku: str, quantidade: int = Query(gt=0)) -> dict[str, bool | int]:
    wsdl = os.getenv("ESTOQUE_WSDL", "http://estoque-legado:8000/?wsdl")
    # TODO: chamar consultarEstoque e devolver disponivel e saldo em JSON.
    raise NotImplementedError
