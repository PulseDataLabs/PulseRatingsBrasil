"""
Preenche coluna cnpj_emissor no consolidado usando dados offline da CVM:
- cad_cia_aberta.csv (cias abertas) — CNPJ_CIA + DENOM_SOCIAL
- cad_fi.csv (fundos) — CNPJ_ADMIN + ADMIN, CPF_CNPJ_GESTOR + GESTOR
"""

import csv
import io
import logging
import re
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import requests

from scripts.consolidar_emissores import normalizar
from utils.paths import get_data_dir

logger = logging.getLogger("preencher_cnpj_cvm")

CVM_CIA_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
CVM_FI_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"
CVM_FUNDO_CLASSE_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"

CACHE_DIR = get_data_dir() / "cvm_cache"
CACHE_TTL = timedelta(hours=24)

COLUNAS_CONSOLIDADO = [
    "no_emissor_padronizado",
    "no_emissor_fitch",
    "no_emissor_moodys",
    "no_emissor_standard_and_poors",
    "no_emissor_austin",
    "no_emissor_liberum",
    "cnpj_emissor",
]


def _limpar_cnpj(valor: str | None) -> str:
    if not valor:
        return ""
    return re.sub(r"\D", "", valor)


def _baixar_csv(url: str, cache_path: Path) -> bool:
    logger.info(f"Baixando {url}...")
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(resp.content)
        logger.info(f"Arquivo salvo em {cache_path} ({len(resp.content)} bytes)")
        return True
    except Exception as e:
        logger.warning(f"Falha ao baixar {url}: {e}")
        return False


def _obter_csv(url: str, filename: str, cache_dir: Path = CACHE_DIR) -> Path | None:
    cache_path = cache_dir / filename
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < CACHE_TTL:
            logger.info(f"Usando cache: {cache_path}")
            return cache_path
    if _baixar_csv(url, cache_path):
        return cache_path
    if cache_path.exists():
        logger.warning(f"Usando cache expirado: {cache_path}")
        return cache_path
    return None


def _ler_csv(caminho: Path, delimiter: str = ";") -> list[dict]:
    with open(caminho, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)


def _carregar_lookup_cias(caminho: Path) -> dict[str, str]:
    rows = _ler_csv(caminho)
    lookup: dict[str, str] = {}
    ambiguos: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        cnpj = _limpar_cnpj(row.get("CNPJ_CIA", ""))
        nome = (row.get("DENOM_SOCIAL") or "").strip()
        if not cnpj or not nome or len(cnpj) != 14:
            continue
        norm = normalizar(nome)
        if not norm:
            continue
        ambiguos[norm].add(cnpj)

    for norm, cnpjs in ambiguos.items():
        if len(cnpjs) == 1:
            lookup[norm] = next(iter(cnpjs))

    if ambiguos:
        mult = {k: v for k, v in ambiguos.items() if len(v) > 1}
        if mult:
            logger.info(f"Cias abertas: {len(mult)} nomes normalizados com múltiplos CNPJs (ignorados)")

    return lookup


def canonical_fund(s: str) -> str:
    """Normaliza abreviações comuns em nomes de fundos (FIDC, FIC, FII, etc.)."""
    norm = normalizar(s)
    if not norm:
        return ""
    norm = re.sub(r"\bFUNDO\s+DE\s+INVESTIMENTO\s+EM\s+DIREITOS\s+CREDITORIOS\b", "FIDC", norm)
    norm = re.sub(r"\bFUNDO\s+INVESTIMENTO\s+DIREITOS\s+CREDITORIOS\b", "FIDC", norm)
    norm = re.sub(r"\bFDO\s+INV\s+DIR\s+CRED\b", "FIDC", norm)
    norm = re.sub(r"\bFUNDO\s+DE\s+INVESTIMENTO\s+EM\s+COTAS\b", "FIC", norm)
    norm = re.sub(r"\bFUNDO\s+INVESTIMENTO\s+COTAS\b", "FIC", norm)
    norm = re.sub(r"\bFUNDO\s+DE\s+INVESTIMENTO\s+IMOBILIARIO\b", "FII", norm)
    norm = re.sub(r"\bFUNDO\s+INVESTIMENTO\s+IMOBILIARIO\b", "FII", norm)
    norm = re.sub(r"\bFUNDO\s+DE\s+INVESTIMENTO\s+EM\s+PARTICIPACOES\b", "FIP", norm)
    norm = re.sub(r"\bFUNDO\s+INVESTIMENTO\s+PARTICIPACOES\b", "FIP", norm)
    norm = re.sub(r"\bFUNDO\s+DE\s+INVESTIMENTO\b", "FI", norm)
    norm = re.sub(r"\bFUNDO\s+INVESTIMENTO\b", "FI", norm)
    norm = re.sub(r"\bRESPONSABILIDADE\s+LIMITADA\b", "", norm)
    norm = re.sub(r"\bRESP\s+LIMITADA\b", "", norm)
    norm = re.sub(r"\bRESP\s+LTDA\b", "", norm)
    norm = re.sub(r"\bNAO\s+PADRONIZAD[OA]S?\b", "NP", norm)
    norm = re.sub(r"\bPADRONIZAD[OA]S?\b", "", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def _iterar_nomes_cnpjs_fundos(
    fi_caminho: Path | None = None,
    fundo_classe_caminho: Path | None = None,
):
    """
    Gera tuplas (nome, cnpj, tipo) para fundos da CVM a partir de cad_fi.csv
    e registro_fundo_classe.zip.
    tipo pode ser 'denom' (denominação do fundo/classe) ou 'admin_gestor' (administrador/gestor).
    """
    if fi_caminho and fi_caminho.exists():
        try:
            for row in _ler_csv(fi_caminho):
                denom = (row.get("DENOM_SOCIAL") or "").strip()
                cnpj_fundo = _limpar_cnpj(row.get("CNPJ_FUNDO") or "")
                if denom and len(cnpj_fundo) == 14:
                    yield denom, cnpj_fundo, "denom"

                for col_nome, col_cnpj in [("ADMIN", "CNPJ_ADMIN"), ("GESTOR", "CPF_CNPJ_GESTOR")]:
                    nome = (row.get(col_nome) or "").strip()
                    cnpj = _limpar_cnpj(row.get(col_cnpj) or "")
                    if nome and len(cnpj) == 14:
                        yield nome, cnpj, "admin_gestor"
        except Exception as e:
            logger.warning(f"Erro ao ler {fi_caminho}: {e}")

    if fundo_classe_caminho and fundo_classe_caminho.exists():
        try:
            with zipfile.ZipFile(fundo_classe_caminho) as z:
                if "registro_fundo.csv" in z.namelist():
                    with z.open("registro_fundo.csv") as f:
                        reader = csv.DictReader(
                            io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"
                        )
                        for row in reader:
                            denom = (row.get("Denominacao_Social") or "").strip()
                            cnpj = _limpar_cnpj(row.get("CNPJ_Fundo") or "")
                            if denom and len(cnpj) == 14:
                                yield denom, cnpj, "denom"
                if "registro_classe.csv" in z.namelist():
                    with z.open("registro_classe.csv") as f:
                        reader = csv.DictReader(
                            io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"
                        )
                        for row in reader:
                            denom = (row.get("Denominacao_Social") or "").strip()
                            cnpj = _limpar_cnpj(row.get("CNPJ_Classe") or "")
                            if denom and len(cnpj) == 14:
                                yield denom, cnpj, "denom"
        except Exception as e:
            logger.warning(f"Erro ao processar {fundo_classe_caminho}: {e}")


def _carregar_lookup_fundos(
    caminho: Path | None,
    fundo_classe_caminho: Path | None = None,
) -> dict[str, str]:
    """
    Lookup exato por nome normalizado de fundos (denominação, admin e gestor).
    Denominações de fundos têm precedência sobre administradores/gestores.
    """
    lookup: dict[str, str] = {}
    ambiguos_denom: dict[str, set[str]] = defaultdict(set)
    ambiguos_admin: dict[str, set[str]] = defaultdict(set)

    for nome, cnpj, tipo in _iterar_nomes_cnpjs_fundos(caminho, fundo_classe_caminho):
        norm = normalizar(nome)
        if not norm:
            continue
        if tipo == "denom":
            ambiguos_denom[norm].add(cnpj)
        else:
            ambiguos_admin[norm].add(cnpj)

    for norm, cnpjs in ambiguos_denom.items():
        if len(cnpjs) == 1:
            lookup[norm] = next(iter(cnpjs))

    for norm, cnpjs in ambiguos_admin.items():
        if norm not in lookup and len(cnpjs) == 1:
            lookup[norm] = next(iter(cnpjs))

    if ambiguos_denom:
        mult = {k: v for k, v in ambiguos_denom.items() if len(v) > 1}
        if mult:
            logger.info(f"Fundos denominação: {len(mult)} nomes normalizados com múltiplos CNPJs (ignorados)")

    return lookup


def _carregar_lookup_fundos_canon(
    caminho: Path | None,
    fundo_classe_caminho: Path | None = None,
) -> dict[str, str]:
    """
    Lookup canônico para variações de fundos (ex: FIDC, NP, RESPONSABILIDADE LIMITADA).
    Apenas mapeamentos 100% não ambíguos são mantidos.
    """
    lookup: dict[str, str] = {}
    ambiguos: dict[str, set[str]] = defaultdict(set)

    for nome, cnpj, tipo in _iterar_nomes_cnpjs_fundos(caminho, fundo_classe_caminho):
        if tipo != "denom":
            continue
        canon = canonical_fund(nome)
        if not canon:
            continue
        ambiguos[canon].add(cnpj)

    for canon, cnpjs in ambiguos.items():
        if len(cnpjs) == 1:
            lookup[canon] = next(iter(cnpjs))

    return lookup


def generate(
    consolidado_path: Path | None = None,
    cache_dir: Path | None = None,
) -> dict:
    if consolidado_path is None:
        consolidado_path = get_data_dir() / "emissores_consolidado.csv"
    if cache_dir is None:
        cache_dir = CACHE_DIR

    logger.info("=" * 50)
    logger.info("PREENCHE CNPJ (CVM)")
    logger.info("=" * 50)

    cia_path = _obter_csv(CVM_CIA_URL, "cad_cia_aberta.csv", cache_dir)
    fi_path = _obter_csv(CVM_FI_URL, "cad_fi.csv", cache_dir)
    fundo_classe_path = _obter_csv(CVM_FUNDO_CLASSE_URL, "registro_fundo_classe.zip", cache_dir)

    lookup_cia: dict[str, str] = {}
    lookup_fi: dict[str, str] = {}
    lookup_canon: dict[str, str] = {}

    if cia_path:
        lookup_cia = _carregar_lookup_cias(cia_path)
        logger.info(f"Cias abertas: {len(lookup_cia)} nomes no lookup")
    else:
        logger.warning("cad_cia_aberta.csv não disponível")

    if fi_path or fundo_classe_path:
        lookup_fi = _carregar_lookup_fundos(fi_path, fundo_classe_path)
        lookup_canon = _carregar_lookup_fundos_canon(fi_path, fundo_classe_path)
        logger.info(
            f"Fundos CVM: {len(lookup_fi)} nomes exatos | {len(lookup_canon)} canônicos no lookup"
        )
    else:
        logger.warning("Arquivos de fundos CVM não disponíveis")

    if not consolidado_path.exists():
        logger.warning(f"Consolidado não encontrado: {consolidado_path}")
        return {"matched": 0, "unmatched": 0, "ambiguous": 0, "total": 0}

    with open(consolidado_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r.pop(None, None)
        r.pop("", None)

    total = len(rows)
    matched = 0
    unmatched = 0
    ambiguous_hits = 0
    updated_rows: list[dict] = []
    ambiguous_list: list[str] = []

    for row in rows:
        if (row.get("cnpj_emissor") or "").strip():
            updated_rows.append(row)
            continue

        nome_pad = (row.get("no_emissor_padronizado") or "").strip()
        if not nome_pad:
            updated_rows.append(row)
            unmatched += 1
            continue

        cnpj = None
        # Priority: 1) cias abertas, 2) fundos nome exato, 3) fundos canônico
        if nome_pad in lookup_cia:
            cnpj = lookup_cia[nome_pad]
        elif nome_pad in lookup_fi:
            cnpj = lookup_fi[nome_pad]
        else:
            canon = canonical_fund(nome_pad)
            if canon in lookup_canon:
                cnpj = lookup_canon[canon]

        if cnpj:
            row["cnpj_emissor"] = cnpj
            matched += 1
        else:
            unmatched += 1

        updated_rows.append(row)

    consolidado_path.parent.mkdir(parents=True, exist_ok=True)
    with open(consolidado_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CONSOLIDADO)
        writer.writeheader()
        writer.writerows(updated_rows)

    logger.info(
        f"Total: {total} | Preenchidos: {matched} | Não encontrados: {unmatched} | Ambíguos: {ambiguous_hits}"
    )
    if ambiguous_list:
        logger.info(f"Ambíguos: {', '.join(ambiguous_list[:10])}{'...' if len(ambiguous_list) > 10 else ''}")

    return {
        "total": total,
        "matched": matched,
        "unmatched": unmatched,
        "ambiguous": ambiguous_hits,
    }


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    result = generate()
    print(f"Resultado: {result['matched']} CNPJs preenchidos de {result['total']} emissores")


if __name__ == "__main__":
    main()
