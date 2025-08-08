from service.soap_service import SoapService
from model.cadastro_model import CadastroModel

class CadastroController:
    def __init__(self):
        self.soap_service = SoapService()
        self.model = CadastroModel()

    def executar(self):
        print("🔄 Buscando cadastros imobiliários...")
        cadastros = self.soap_service.buscar_cadastros()
        self.model.salvar_json(cadastros)
        print(f"✅ {len(cadastros)} cadastros salvos em data/cadastros.json")
