import json
import os

class CadastroModel:
    def __init__(self):
        self.output_path = os.path.join("data", "cadastros.json")

    def salvar_json(self, dados):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
