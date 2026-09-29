import os

from fastapi import FastAPI, HTTPException, Query
from zeep import Client

app = FastAPI(title="Adapter de estoque")


@app.get("/estoques/{sku}")
def consultar_estoque(sku: str, quantidade: int = Query(gt=0)) -> dict[str, bool | int]:
    wsdl = os.getenv("ESTOQUE_WSDL", "http://estoque-legado:8000/?wsdl")
    try:
        cliente = Client(wsdl)
        resultado = cliente.service.consultarEstoque(sku=sku, quantidade=quantidade)
    except Exception as erro:
        raise HTTPException(status_code=503, detail="Estoque indisponível") from erro
    return {"disponivel": bool(resultado.disponivel), "saldo": int(resultado.saldo)}
