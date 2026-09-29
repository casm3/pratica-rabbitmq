import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import urlopen

import pika


def consultar_estoque(produto: str, quantidade: int) -> dict[str, Any]:
    base = os.getenv("ESTOQUE_ADAPTER_URL", "http://estoque-adapter:8000")
    sku = quote(produto, safe="")
    parametros = urlencode({"quantidade": quantidade})
    url = f"{base}/estoques/{sku}?{parametros}"

    with urlopen(url, timeout=5) as resposta:
        return json.load(resposta)


def processar(canal: Any, metodo: Any, propriedades: Any, corpo: bytes) -> None:
    evento = json.loads(corpo.decode("utf-8"))
    pedido = evento["dados"]

    print(f"Processando pedido {pedido['id']}...", flush=True)

    try:
        estoque = consultar_estoque(
            produto=pedido["produto"],
            quantidade=pedido["quantidade"],
        )
    except (HTTPError, URLError, TimeoutError) as erro:
        print(
            f"Pedido {pedido['id']}: falha ao consultar estoque: {erro}",
            flush=True,
        )
        canal.basic_nack(delivery_tag=metodo.delivery_tag, requeue=True)
        time.sleep(2)
        return

    if not estoque["disponivel"]:
        print(
            f"Pedido {pedido['id']}: rejeitado. "
            f"Quantidade solicitada: {pedido['quantidade']}; "
            f"saldo disponível: {estoque['saldo']}.",
            flush=True,
        )
        canal.basic_ack(delivery_tag=metodo.delivery_tag)
        return

    print(
        f"Pedido {pedido['id']}: confirmação enviada para {pedido['email']}",
        flush=True,
    )
    canal.basic_ack(delivery_tag=metodo.delivery_tag)


def iniciar() -> None:
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")

    while True:
        try:
            conexao = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            break
        except pika.exceptions.AMQPConnectionError:
            print("Aguardando RabbitMQ...", flush=True)
            time.sleep(2)

    canal = conexao.channel()
    canal.queue_declare(queue="pedidos", durable=True)
    canal.basic_qos(prefetch_count=1)
    canal.basic_consume(
        queue="pedidos",
        on_message_callback=processar,
        auto_ack=False,
    )

    print("Aguardando pedidos...", flush=True)
    canal.start_consuming()


if __name__ == "__main__":
    iniciar()