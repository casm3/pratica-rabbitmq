# 🚀 Lista de Exercícios: Pedidos, Mensageria e Estoque

**Integração de Sistemas**

1. Suba o ambiente:
   ```bash
   docker compose up -d --build
   ```
2. Abra as portas de controle no seu navegador:
   * **API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
   * **Painel do RabbitMQ:** [http://localhost:15672](http://localhost:15672) *(login e senha: `guest`)*
   * **Contrato do Estoque (SOAP):** [http://localhost:8001/?wsdl](http://localhost:8001/?wsdl)

3. Faça o primeiro teste: vá ao Swagger da API e envie um **`POST /pedidos`** com o payload:
   ```json
   {
     "cliente": "Ana",
     "email": "ana@email.com",
     "produto": "NOTEBOOK",
     "quantidade": 2
   }
   ```
   Você deve receber um status **`202 Accepted`** com `status: recebido`. 

4. Agora abra o painel do RabbitMQ, acesse **Queues and Streams → pedidos** e dê uma olhada nos contadores: **Ready**, **Unacked** e **Consumers**. 
   * *O que está acontecendo aqui?* Como ainda não criamos nenhum consumidor, a mensagem deve ficar parada aguardando na fila.

> ⚠️ **Atenção:** A API guarda os pedidos apenas na memória. Se o contêiner for recriado, a contagem de IDs volta do zero. Use sempre o ID que aparecer nos seus próprios testes e evite rodar `docker compose down -v`.

---

## 1. 📬 Recebendo a Primeira Mensagem

1. Complete o script `notificacoes/consumer.py` e adicione o serviço `notificacoes` ao seu `compose.yaml`.
2. O consumidor precisa:
   * Conectar-se ao host apontado pela variável `RABBITMQ_HOST`.
   * Declarar a fila durável `pedidos`.
   * Ficar escutando continuamente, converter o payload JSON e imprimir no terminal o **ID do pedido** e o **e-mail do cliente**.
   * Depender do serviço `rabbitmq` no Compose e usar o `Dockerfile` da própria pasta.
3. Suba o serviço e acompanhe os logs:
   ```bash
   docker compose up -d --build notificacoes
   docker compose logs -f notificacoes
   ```

4. **Para registrar no relatório:** Volte ao painel do RabbitMQ e anote os três contadores. Explique com suas palavras: *por que a API conseguiu responder ao cliente no Swagger antes mesmo de o consumidor existir?*

---

## 2. 🛑 Trabalhando com Garantias (Acks e Interrupções)

1. **Parada inicial:** Pare o consumidor com `docker compose stop notificacoes` e envie **3 novos pedidos** pelo Swagger.
2. Antes de subir o consumidor de novo, olhe o painel do RabbitMQ: quantas mensagens estão em **Ready**? Quantos **Consumers** estão ativos?
3. Religue com `docker compose start notificacoes` e confira os logs zerando a fila.

### Entendendo o Confirm (Ack)
Agora, adicione um `sleep` de 5 segundos no consumidor, exatamente entre a mensagem `"Processando pedido..."` e a confirmação final no log.

* **Cenário A (`auto_ack=True`):**
  Configure o consumo com `auto_ack=True`. Envie um pedido e, **durante a pausa de 5 segundos**, mate o contêiner na força bruta:
  ```bash
  docker compose kill notificacoes
  ```
  O que aconteceu com os números de **Ready** e **Unacked** no painel? A confirmação chegou a ser concluída? A mensagem continuou na fila?

* **Cenário B (`auto_ack=False`):**
  Altere o código para `auto_ack=False` e envie o `basic_ack` **apenas depois** da confirmação no terminal. Repita a interrupção no meio do `sleep`.
  Anote o comportamento dos contadores:
  1. Enquanto a mensagem está sendo processada.
  2. Logo após o `kill`.
  3. Depois de iniciar o consumidor novamente.

* **Para registrar no relatório:** Por que o mesmo pedido acabou sendo entregue de novo? O que pode dar errado no mundo real se a gente avisar o cliente que deu tudo certo, mas o serviço cair antes de mandar o `ack` pro RabbitMQ?

---

## 3. 📜 Decifrando o Serviço Legado (SOAP)

Nosso controle de estoque roda em um sistema mais antigo usando o protocolo SOAP.

1. Abra `http://localhost:8001/?wsdl` no navegador e busque pela operação `consultarEstoque`. Note os parâmetros `sku` e `quantidade`.
   *(Curiosidade: esse estoque fictício tem 5 NOTEBOOKs, 10 TECLADOs e 20 MOUSEs).*
2. Adicione temporariamente a biblioteca `zeep>=4.2,<5` ao `pedidos/requirements.txt`.
3. Crie um script rápido em `pedidos/cliente_estoque.py` para consultar o SKU `NOTEBOOK` em duas situações: quantidade **2** e quantidade **20**. *(Dentro da rede do Compose, o WSDL fica em `http://estoque-legado:8000/?wsdl`)*.
4. Execute o script via container:
   ```bash
   docker compose build pedidos
   docker compose run --rm pedidos python cliente_estoque.py
   ```

---

## 4. 🔄 Isolando o Legado com um Adapter

Para não poluir a API de pedidos com SOAP, vamos criar um Adapter que transforma tudo em JSON/REST.

1. Complete `estoque_adapter/main.py` e adicione o serviço `estoque-adapter` ao Compose (mapeado na porta externa `8002` e configurado com `ESTOQUE_WSDL=http://estoque-legado:8000/?wsdl`).
2. Crie o endpoint `GET /estoques/{sku}` recebendo `quantidade` (inteiro positivo). Ele deve chamar o serviço legado e responder em JSON limpo com `disponivel` e `saldo`. Caso o legado esteja fora do ar, retorne `503 Service Unavailable`.
3. Suba o adapter:
   ```bash
   docker compose up -d --build estoque-adapter
   ```
4. Teste a nova API REST em `http://localhost:8002/docs` consultando `NOTEBOOK` com quantidades **2** e **20**. Ambas devem responder `200 OK` (mesmo que uma diga `disponivel: false`).

---

## 5. 🛑 Validação Prévia: Checando Estoque Antes de Aceitar

1. Atualize `pedidos/main.py`: antes de publicar a mensagem no RabbitMQ, a API deve fazer uma requisição HTTP para o nosso Adapter.
2. Adicione `ESTOQUE_URL=http://estoque-adapter:8000` no Compose.
3. Limpeza: troque o `zeep` por `httpx>=0.27,<1` no `pedidos/requirements.txt` e apague o script temporário `cliente_estoque.py`. Toda a lógica SOAP agora fica isolada no Adapter!
4. Mantenha a estrutura original do evento `pedido.criado`.

Abra o Swagger da API (`http://localhost:8000/docs`) e valide as três situações:

| Pedido Enviado          | Resposta Esperada                     | O que verificar                                               |
| :---------------------- | :------------------------------------ | :------------------------------------------------------------ |
| **NOTEBOOK** (qtd: 2)   | `202 Accepted` (`status: recebido`)   | Aparece no `GET /pedidos` e chega no serviço de notificações. |
| **NOTEBOOK** (qtd: 100) | `409 Conflict` (estoque insuficiente) | **Não** é salvo na API e **não** gera mensagem no RabbitMQ.   |
| **MONITOR** (qtd: 1)    | `409 Conflict` (estoque insuficiente) | O legado retorna saldo zero para produtos não cadastrados.    |

> 💡 **Dica de teste:** Acompanhe a fila no RabbitMQ a cada chamada. Se quiser ver as mensagens se acumulando sem serem consumidas imediatamente, dê um `stop` no container `notificacoes` antes de testar.

---

## 6. 💥 Lidando com Instabilidades (Resiliência)

O que acontece se o sistema de estoque cair?

1. Derrube o serviço legado:
   ```bash
   docker compose stop estoque-legado
   ```
2. Tente criar um pedido válido no Swagger. A API de pedidos deve responder **`503 Service Unavailable`**, garantindo que nenhum pedido sem validação seja aceito ou publicado na fila.
3. Teste também a resposta direta do adapter em `http://localhost:8002/docs`.
4. Suba o legado novamente com `docker compose start estoque-legado` e confirme que o fluxo volta ao normal.

* **Para registrar no relatório:**
  * Por que a consulta de estoque precisa acontecer **sincronamente** (antes de responder ao cliente), enquanto a notificação roda de forma **assíncrona** (depois)?
  * Qual serviço do projeto precisa conhecer SOAP e qual lida estritamente com JSON?

---
