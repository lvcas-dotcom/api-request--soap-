"""
Cliente SOAP Completo para Integração Cadastral (modo raw XML)
- Evita erro de datas BR (DD/MM/YYYY) no Zeep convertendo após o parse
- Implementa fallbacks de operações e extração robusta de arrays
- Aceita kwargs extras (paginação etc. quando existir)
"""

import logging
import re
import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings
from zeep.exceptions import Fault as SOAPFault
from zeep.transports import Transport
from lxml import etree as ET

from config.settings import settings


class SOAPClientError(Exception):
    pass


# ---------------- Normalização de datas/textos ----------------
_DATE_BR_RE = re.compile(r"^\d{2}/\d{2}/\d{4}(?: \d{2}:\d{2}:\d{2})?$")
_DATE_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATE_ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def _to_iso_date_if_needed(s: str) -> str:
    """Converte 'DD/MM/YYYY[ HH:MM:SS]' -> 'YYYY-MM-DD[ HH:MM:SS]'."""
    if not isinstance(s, str):
        return s
    if _DATE_BR_RE.match(s):
        try:
            if " " in s:
                dt = datetime.strptime(s, "%d/%m/%Y %H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                d = datetime.strptime(s, "%d/%m/%Y").date()
                return d.strftime("%Y-%m-%d")
        except Exception:
            return s
    # mantém ISO se já estiver
    if _DATE_ISO_DATE_RE.match(s) or _DATE_ISO_DATETIME_RE.match(s):
        return s
    return s


def _normalize_obj(obj: Any) -> Any:
    """Normaliza recursivamente: strings de data BR -> ISO."""
    if obj is None:
        return None
    if isinstance(obj, (int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, str):
        return _to_iso_date_if_needed(obj)
    if isinstance(obj, list):
        return [_normalize_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _normalize_obj(v) for k, v in obj.items()}
    return obj


# ---------------- Parse e helpers ----------------
def _local(tag: str) -> str:
    """Extrai localname ignorando namespace."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _elem_to_obj(elem: ET._Element) -> Any:
    """Converte um elemento XML em dict/list/str, ignorando namespaces, preservando repetições."""
    children = [c for c in elem if isinstance(c.tag, str)]
    if not children:
        text = (elem.text or "").strip()
        return _to_iso_date_if_needed(text)

    out: Dict[str, Any] = {}
    for child in children:
        key = _local(child.tag)
        val = _elem_to_obj(child)
        if key in out:
            # vira lista quando repetido
            if not isinstance(out[key], list):
                out[key] = [out[key]]
            out[key].append(val)
        else:
            out[key] = val
    return out


def _parse_soap_response(xml_bytes: bytes) -> Any:
    """Recebe bytes do SOAP e retorna o conteúdo do Body (primeiro filho) como dict."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.XMLSyntaxError as e:
        raise SOAPClientError(f"XML inválido: {e}") from e

    # Busca Body (qualquer namespace)
    body = root.find(".//{*}Body")
    if body is None:
        return _elem_to_obj(root)

    payloads = [c for c in body if isinstance(c.tag, str)]
    if not payloads:
        return {}
    return _elem_to_obj(payloads[0])  # ex.: buscaXResponse


def _unwrap_return(resp: Any) -> Any:
    """Se houver wrapper de retorno, desembrulha."""
    if not isinstance(resp, dict):
        return resp
    # comum: {'return': {...}}
    if "return" in resp and isinstance(resp["return"], (dict, list)):
        return resp["return"]
    # às vezes: {'retorno': {...}}
    if "retorno" in resp and isinstance(resp["retorno"], (dict, list)):
        return resp["retorno"]
    return resp


def _to_list(value: Any) -> List[Any]:
    """Normaliza qualquer 'array SOAP' para lista Python."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        # padrão: {'item': [...]} ou {'cadastros': [...]} ou único dict
        if "item" in value:
            v = value["item"]
            return v if isinstance(v, list) else [v]
        # se houver exatamente um campo e ele for lista, usa
        if len(value) == 1:
            only = next(iter(value.values()))
            if isinstance(only, list):
                return only
        # último recurso: um único objeto
        return [value]
    # valor simples vira lista de 1
    return [value]


def _extract_first(resp: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in resp:
            return resp[k]
    return None


class CadastralSOAPClient:
    """Client SOAP com raw_response=True para contornar datas BR e arrays SOAP."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._build_client()
        # retries e delay com fallback seguro
        self.retry_attempts = int(
            getattr(
                settings.soap,
                "retry_attempts",
                getattr(settings.soap, "max_retries", 3),
            )
        )
        self.retry_delay = float(getattr(settings.soap, "retry_delay", 0.5))

    def _build_client(self):
        session = Session()
        if settings.soap.username and settings.soap.password:
            session.auth = HTTPBasicAuth(settings.soap.username, settings.soap.password)

        transport = Transport(
            session=session, timeout=getattr(settings.soap, "timeout", 30)
        )
        zeep_settings = Settings(
            strict=False,
            xml_huge_tree=True,
            raw_response=True,  # <<< ESSENCIAL
        )
        self.client = Client(
            wsdl=settings.soap.wsdl_path, settings=zeep_settings, transport=transport
        )

        # Override endpoint (se configurado)
        if settings.soap.endpoint_url:
            for service in self.client.wsdl.services.values():
                for port in service.ports.values():
                    port.binding_options["address"] = settings.soap.endpoint_url

    def _call(self, op_main: str, op_fallbacks: List[str], **kwargs) -> Any:
        last_err: Optional[Exception] = None
        ops = [op_main] + (op_fallbacks or [])
        for _ in range(max(self.retry_attempts, 1)):
            for name in ops:
                try:
                    op = getattr(self.client.service, name)
                    self.logger.debug(f"[SOAP] Chamando {name} kwargs={kwargs}")
                    resp = op(
                        **kwargs
                    )  # raw_response=True => requests.Response-like ou bytes
                    xml_bytes = getattr(resp, "content", resp)
                    parsed = _parse_soap_response(xml_bytes)
                    parsed = _unwrap_return(parsed)
                    return _normalize_obj(parsed)
                except AttributeError as e:
                    last_err = e
                except SOAPFault as e:
                    last_err = e
                    self.logger.warning(f"[SOAP] Fault em {name}: {e}")
                except Exception as e:
                    last_err = e
                    self.logger.warning(f"[SOAP] Erro em {name}: {e}")
            time.sleep(self.retry_delay)
        raise SOAPClientError(f"Falha ao chamar {op_main}/{op_fallbacks}: {last_err}")

    # ---------------- Operações ----------------

    def buscar_cadastro_geral(
        self,
        codigo_cadastro: Optional[str] = None,
        tipo_consulta: Optional[int] = None,
        situacao: Optional[int] = None,
        **kwargs,
    ) -> List[Dict]:
        """
        WSDL: buscaCadastroImobiliarioGeral (+ fallbacks)
        Aceita kwargs para compat futura (pagina/qtd, offset/limit, etc.)
        """
        entrada = {
            "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
            "codigo_cadastro": codigo_cadastro,
            "tipo_consulta": tipo_consulta,
            "situacao": situacao,
        }
        # demais filtros possíveis no WSDL (se quiser usar no futuro):
        for opt in (
            "inscricao_imobiliaria",
            "proprietario_cpfcnpj",
            "codigo_terreno",
            "data_hora_alteracao",
        ):
            if kwargs.get(opt) not in (None, ""):
                entrada[opt] = kwargs[opt]

        payload = {"entrada": {k: v for k, v in entrada.items() if v not in (None, "")}}

        resp = self._call(
            "buscaCadastroImobiliarioGeral",
            ["buscaCadastroImobiliarioGeralBCI"],
            **payload,
        )
        if isinstance(resp, dict):
            lst = _extract_first(resp, "cadastros", "lista", "retorno", "cadastro")
            return _to_list(lst)
        return _to_list(resp)

    def buscar_cadastro_especifico(self, codigo_cadastro: str) -> Optional[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call(
            "buscaCadastroImobiliario", ["buscaCadastroImobiliarioBCI"], **payload
        )
        return resp or None

    def _extract_list_by_keys(self, resp: Any, *keys: str) -> List[Dict]:
        """Helper genérico para extrair lista por chaves comuns."""
        if not isinstance(resp, dict):
            return _to_list(resp)
        inner = _extract_first(resp, *keys)
        return _to_list(inner)

    def buscar_proprietarios(self, codigo_cadastro: str) -> List[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call("buscaProprietarios", ["buscaProprietarioBCI"], **payload)
        return self._extract_list_by_keys(resp, "proprietarios", "proprietario")

    def buscar_enderecos(self, codigo_cadastro: str) -> List[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call("buscaEnderecoImovel", ["buscaEnderecoBCI"], **payload)
        return self._extract_list_by_keys(resp, "enderecos", "endereco")

    def buscar_testadas(self, codigo_cadastro: str) -> List[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call("buscaTestadas", ["buscaTestadaBCI"], **payload)
        return self._extract_list_by_keys(resp, "testadas", "testada")

    def buscar_subreceitas(self, codigo_cadastro: str) -> List[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call(
            "buscaSubReceitas", ["buscaSubreceitaBCI", "buscaSubReceitaBCI"], **payload
        )
        return self._extract_list_by_keys(resp, "subreceitas", "subreceita")

    def buscar_zoneamentos(self, codigo_cadastro: str) -> List[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call("buscaZoneamento", ["buscaZoneamentoBCI"], **payload)
        return self._extract_list_by_keys(resp, "zoneamentos", "zoneamento")

    def buscar_anexos(self, codigo_cadastro: str) -> List[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call("buscaAnexos", ["buscaAnexoBCI", "buscaAnexosBCI"], **payload)
        return self._extract_list_by_keys(resp, "anexos", "anexo")

    def buscar_historico(self, codigo_cadastro: str) -> List[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call("buscaHistorico", ["buscaHistoricoBCI"], **payload)
        return self._extract_list_by_keys(resp, "historicos", "historico")

    def buscar_bloco_itens(self, codigo_cadastro: str) -> List[Dict]:
        payload = {
            "entrada": {
                "cpf_monitoracao": getattr(settings, "cpf_monitoracao", None),
                "codigo_cadastro": codigo_cadastro,
            }
        }
        resp = self._call("buscaBlocoItens", ["buscaBlocoItensBCI"], **payload)
        return self._extract_list_by_keys(resp, "blocoItens", "itens", "blocoItem")

    def buscar_itbi(
        self,
        codigo_cadastro: str,
        inscricao_imobiliaria: Optional[str] = None,
        numero_itbi: Optional[int] = None,
        ano_itbi: Optional[int] = None,
        data_itbi: Optional[str] = None,
    ) -> List[Dict]:
        """
        WSDL: buscaItbiCadastroImobiliario
        ATENÇÃO: este método NÃO aceita cpf_monitoracao. O tipo de entrada é 'entradaBuscaItbiCadbci'
        com os campos: codigo_cadastro, inscricao_imobiliaria, numero_itbi, ano_itbi, data_itbi.
        """
        # monta somente os campos aceitos pela assinatura
        entrada = {
            "codigo_cadastro": (
                int(codigo_cadastro)
                if str(codigo_cadastro).isdigit()
                else codigo_cadastro
            )
        }
        if inscricao_imobiliaria:
            entrada["inscricao_imobiliaria"] = str(inscricao_imobiliaria)
        if numero_itbi is not None:
            entrada["numero_itbi"] = int(numero_itbi)
        if ano_itbi is not None:
            entrada["ano_itbi"] = int(ano_itbi)
        if data_itbi:
            # aceita 'DD/MM/YYYY' ou 'YYYY-MM-DD'; normalizamos se vier BR
            entrada["data_itbi"] = _to_iso_date_if_needed(data_itbi)

        # 1ª tentativa: com wrapper 'entrada'
        try:
            resp = self._call("buscaItbiCadastroImobiliario", [], entrada=entrada)
        except SOAPClientError:
            # 2ª tentativa (alguns WSDLs não usam wrapper): sem 'entrada'
            resp = self._call("buscaItbiCadastroImobiliario", [], **entrada)

        # extrai lista por chaves comuns
        if isinstance(resp, dict):
            lst = (
                resp.get("itbis")
                or resp.get("listaItbi")
                or resp.get("itbi")
                or resp.get("retorno")
                or resp.get("lista")
            )
            if lst is None:
                # alguns retornam um único objeto
                return [resp]
            return lst if isinstance(lst, list) else [lst]
        return resp or []
