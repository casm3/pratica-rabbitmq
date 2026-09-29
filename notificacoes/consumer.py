import json
import os
import time
from typing import Any

import pika


def processar(canal: Any, metodo: Any, propriedades: Any, corpo: bytes) -> None:
    evento = json.loads(corpo.decode("utf-8"))
    pedido = evento["dados"]
    print(f"Processando pedido {pedido['id']}...", flush=True)
    time.sleep(5)
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
    canal.basic_consume(queue="pedidos", on_message_callback=processar, auto_ack=False)
    print("Aguardando pedidos...", flush=True)
    canal.start_consuming()


if __name__ == "__main__":
    iniciar()
