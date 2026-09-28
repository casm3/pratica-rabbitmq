import os
import time
from typing import Any

import pika


def processar(
        canal: Any,
        metodo: Any,
        propriedades: Any,
        corpo: bytes
        ) -> None:
    # TODO: decodificar o JSON, mostrar a confirmação e enviar o ack.
    raise NotImplementedError


def iniciar() -> None:
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    # TODO: conectar, declarar a fila pedidos e iniciar o consumo.
    raise NotImplementedError


if __name__ == "__main__":
    iniciar()
