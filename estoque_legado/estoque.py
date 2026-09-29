from wsgiref.simple_server import make_server

from spyne import Application, Boolean, ComplexModel, Integer, ServiceBase, Unicode, rpc
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication


class ResultadoEstoque(ComplexModel):
    disponivel = Boolean
    saldo = Integer


class Estoque(ServiceBase):
    @rpc(Unicode, Integer, _returns=ResultadoEstoque)
    def consultarEstoque(ctx, sku: str, quantidade: int) -> ResultadoEstoque:
        saldos = {"NOTEBOOK": 5, "TECLADO": 10, "MOUSE": 20}
        saldo = saldos.get(sku.upper(), 0)
        return ResultadoEstoque(disponivel=saldo >= quantidade, saldo=saldo)


aplicacao = Application(
    [Estoque], tns="urn:estoque", in_protocol=Soap11(), out_protocol=Soap11()
)

if __name__ == "__main__":
    servidor = make_server("0.0.0.0", 8000, WsgiApplication(aplicacao))
    print("Estoque SOAP em http://localhost:8000/?wsdl", flush=True)
    servidor.serve_forever()
