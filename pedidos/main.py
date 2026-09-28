import json
import os
import uuid
from typing import Any

import pika
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Pedidos")
pedidos: list[dict[str, Any]] = []


class NovoPedido(BaseModel):
    cliente: str
    email: str
    produto: str
    quantidade: int = Field(default=1, gt=0)


def publicar(evento: dict[str, Any]) -> None:
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    conexao = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    try:
        canal = conexao.channel()
        canal.queue_declare(queue="pedidos", durable=True)
        canal.basic_publish(
            exchange="",
            routing_key="pedidos",
            body=json.dumps(evento).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        conexao.close()


@app.get("/")
def inicio() -> dict[str, str]:
    return {"mensagem": "API em execução"}


@app.get("/pedidos")
def listar_pedidos() -> list[dict[str, Any]]:
    return pedidos


@app.post("/pedidos", status_code=status.HTTP_202_ACCEPTED)
def criar_pedido(pedido: NovoPedido) -> dict[str, int | str]:
    identificador = len(pedidos) + 1
    dados = pedido.model_dump()
    dados["id"] = identificador
    evento = {
        "mensagem_id": str(uuid.uuid4()),
        "tipo": "pedido.criado",
        "versao": 1,
        "dados": dados,
    }
    try:
        publicar(evento)
    except pika.exceptions.AMQPError as erro:
        raise HTTPException(
            status_code=503,
            detail="Fila indisponível"
        ) from erro
    pedidos.append(dados)
    return {"id": identificador, "status": "recebido"}
