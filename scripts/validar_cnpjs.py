"""
Valida os CNPJs do consolidado contra a base RFB + CVM.

Para cada CNPJ no emissores_consolidado.csv, consulta a razão social
na Receita Federal (empresas.db) e opcionalmente na CVM (cad_fi.csv),
compara com o nome padronizado, e gera um relatório.
"""

import csv
import logging
import re
import sqlite3
import unicodedata
from collections import defaultdict

from scripts.consolidar_emissores import _PALAVRAS_GENERICAS, _SUFIXOS, normalizar
from utils.paths import get_data_dir

logger = logging.getLogger("validar_cnpjs")

DATA_DIR = get_data_dir()
CONSOLIDADO_PATH = DATA_DIR / "emissores_consolidado.csv"
RFB_DB_PATH = DATA_DIR / "rfb_cache" / "empresas.db"
CVM_CIA_PATH = DATA_DIR / "cvm_cache" / "cad_cia_aberta.csv"
CVM_FI_PATH = DATA_DIR / "cvm_cache" / "cad_fi.csv"
RELATORIO_PATH = DATA_DIR / "validacao_cnpjs.csv"

# Padrão pra detectar ano/série no final do nome
_RE_ANO = re.compile(r"\s+\d{4}$")
_RE_ROMANO = re.compile(r"\s+(I{1,3}|IV|V|VI{0,3}|X)$")
_RE_TRAILING_DOT = re.compile(r"\.$")

# Padrões de boilerplate de FIDC/fundos para _normalizar_leniente
_FIDC_PATTERNS = [
    re.compile(r"\bFUNDO\s+DE\s+INVESTIMENTO\s+EM\s+DIREITOS\s+CREDITORIOS\b"),
    re.compile(r"\bFUNDO\s+DE\s+INVESTIMENTO\b"),
    re.compile(r"\bINVESTIMENTO\s+EM\s+DIREITOS\s+CREDITORIOS\b"),
    re.compile(r"\bDIREITOS\s+CREDITORIOS\s+COMERCIAIS\b"),
    re.compile(r"\bDIREITOS\s+CREDITORIOS\b"),
    re.compile(r"\bCREDITO\s+MERCANTIL\b"),
    re.compile(r"\bDE\s+RESPONSABILIDADE\s+LIMITADA\b"),
    re.compile(r"\bRESPONSABILIDADE\s+LIMITADA\b"),
    re.compile(r"\bRESP\s+LTDA\b"),
    re.compile(r"\bSEGMENTO\s+(?:FINANCEIRO|MEIOS\s+DE\s+PAGAMENTO)\b"),
    re.compile(r"\bMEIOS\s+DE\s+PAGAMENTO\b"),
    re.compile(r"\bCLASSE\s+UNICA\b"),
    re.compile(r"\bDE\s+CLASSE\s+UNICA\b"),
]

# Stop words adicionais para a comparação leniente
_PALAVRAS_LENIENTE = _PALAVRAS_GENERICAS + [
    # FIDC boilerplate
    r"\bFUNDO\b",
    r"\bINVESTIMENTO\b",
    r"\bDIREITOS\b",
    r"\bCREDITORIOS\b",
    r"\bFIDC\b",
    r"\bFICFIDC\b",
    r"\bSEGMENTO\b",
    r"\bFINANCEIROS?\b",
    r"\bMEIOS\b",
    r"\bPAGAMENTO\b",
    r"\bRESP\b",
    r"\bRESPONSBILIDADE\b",
    r"\bRESPONSABILIDADE\b",
    r"\bLIMITADA\b",
    r"\bCLASSE\b",
    r"\bUNICA\b",
    r"\bFECHADA\b",
    r"\bCOMERCIAIS\b",
    r"\bCREDITO\b",
    r"\bMERCANTIL\b",
    r"\bCONSUMIDOR\b",
    r"\bEMPRESARIAL\b",
    r"\bTRANSACOES\b",
    r"\bRECEBIVEIS\b",
    r"\bSUSTENTAVEL\b",
    r"\bGREEN\b",
    r"\bESG\b",
    r"\bIS\b",
    # Companhias/empresas genéricas
    r"\bCOMPANHIA\b",
    r"\bCIA\b",
    r"\bEMPRESA\b",
    r"\bEMPREENDIMENTOS\b",
    r"\bSOCIEDADE\b",
    # Securitização
    r"\bSECURITIZADORA\b",
    r"\bSECURITIZACAO\b",
    r"\bSECURITISATION\b",
    # Energia/transmissão
    r"\bENERGIA\b",
    r"\bELETRICA\b",
    r"\bTRANSMISSAO\b",
    r"\bTRANSMISSORA\b",
    r"\bSUBHOLDING\b",
    # Participações/gestão
    r"\bPARTICIPACOES\b",
    r"\bPART\b",
    r"\bHOLDING\b",
    r"\bADMINISTRACAO\b",
    r"\bADMIN\b",
    r"\bADMINISTRADORA\b",
    r"\bGESTORA\b",
    r"\bGESTAO\b",
    r"\bASSET\b",
    r"\bMANAGEMENT\b",
    r"\bDTVM\b",
    r"\bDISTRIBUIDORA\b",
    r"\bTITULOS\b",
    r"\bVALORES\b",
    r"\bMOBILIARIOS\b",
    # Outras genéricas
    r"\bASSESSORIA\b",
    r"\bCONSULTORIA\b",
    r"\bSERVICOS\b",
    r"\bCOMERCIAL\b",
    r"\bIMPORTADORA\b",
    r"\bBENEF\b",
    r"\bBENEFICENTE\b",
    r"\bHOSPITAL\b",
    r"\bECON\b",
    r"\bECONOMIA\b",
    r"\bCRED\b",
    r"\bMUTUO\b",
    r"\bDESENVOLVIMENTO\b",
    r"\bHABITACIONAL\b",
    r"\bURBANO\b",
    r"\bMUNICIPALITY\b",
    r"\bMUNICIPIO\b",
    r"\bSTATE\b",
    r"\bESTADO\b",
]

# Mapa de renomes históricos conhecidos
_RENAMES: dict[str, str] = {
    "GAIA": "PLANETA",
    "VIRGO": "RIZA",
    "WESTERN ASSET": "FRANKLIN TEMPLETON",
    "TRUSTHUB": "SRM SEC",
    "AMBIPAR LUX": "AMBIPAR PARTICIPACOES",
    "NOVA SECURITISATION": "NOVA SECURITIZADORA",
    "TRUE SECURITIZADORA": "TRUE ADMINISTRADORA",
    "DMCARD": "DM",
    "ELETROBRAS CHESF": "AXIA ENERGIA NORDESTE",
    "CEA II": "ASSURUA 2 ENERGIA",
    "CENTRAIS ELETRICAS BRASILEIRAS": "AXIA ENERGIA",
}


def _cnpj_base(cnpj: str) -> str:
    limpo = re.sub(r"\D", "", cnpj)
    return limpo[:8]


def _cnpj_completo(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj)


def _sem_ano(nome: str) -> str:
    nome = _RE_ANO.sub("", nome)
    nome = _RE_ROMANO.sub("", nome)
    return nome.strip()


def _sem_ano_rfb(nome: str) -> str:
    """Remove ano do nome RFB também."""
    return _sem_ano(nome)


def _strip_genericas(palavras: set) -> set:
    return {p for p in palavras if len(p) >= 2}


def _normalizar_leniente(nome: str) -> str:
    if not nome or not nome.strip():
        return ""
    result = nome.upper().strip()
    result = result.replace("\u2013", "-").replace("\u2014", "-")
    result = result.replace("&", " ")

    result = unicodedata.normalize("NFKD", result)
    result = result.encode("ascii", "ignore").decode("ascii")

    result = re.sub(r"\([^)]*\)", "", result)

    for pattern in _SUFIXOS:
        result = re.sub(pattern, "", result)

    for pattern in _FIDC_PATTERNS:
        result = pattern.sub("", result)

    # Remove trailing period and clean hyphens/separators
    result = _RE_TRAILING_DOT.sub("", result)
    result = result.replace(" - ", " ").replace(" -", " ").replace("- ", " ")

    for pattern in _PALAVRAS_LENIENTE:
        result = re.sub(pattern, "", result)

    result = re.sub(r"\s+", " ", result).strip()

    return result


def _is_acronym(short: str, long: str) -> bool:
    """Verifica se short é sigla de long (ex: CDHU ≈ COMPANHIA DESENVOLVIMENTO HABITACIONAL URBANO)."""
    words = long.split()
    initials = "".join(w[0] for w in words if w[0].isalpha())
    return len(short) >= 2 and initials == short.upper()


def _comparar_nomes(nome_csv: str, nome_rfb: str) -> tuple[str, str]:
    n_csv = normalizar(nome_csv)
    n_rfb = normalizar(nome_rfb)

    if not n_csv or not n_rfb:
        return "❓", "nome vazio"

    # --- Stage 1: strict exact ---
    if n_csv == n_rfb:
        return "✅", "match exato"

    # --- Stage 2: strict sem sufixo ano/romano ---
    n_csv_ss = normalizar(_sem_ano(nome_csv))
    if n_csv_ss and n_csv_ss == n_rfb:
        return "✅", "match exato (sem sufixo)"
    n_rfb_ss = normalizar(_sem_ano(nome_rfb))
    if n_rfb_ss and n_rfb_ss == n_csv:
        return "✅", "match exato (sem sufixo RFB)"

    # --- Stage 3: lenient exact ---
    n_csv_len = _normalizar_leniente(nome_csv)
    n_rfb_len = _normalizar_leniente(nome_rfb)
    if n_csv_len and n_rfb_len and n_csv_len == n_rfb_len:
        return "✅", "match exato (leniente)"

    # --- Stage 4: substring leniente ---
    if n_csv_len and n_rfb_len and (n_csv_len in n_rfb_len or n_rfb_len in n_csv_len):
        return "⚠️", "match parcial (substring leniente)"

    # --- Stage 5: substring strict ---
    if n_csv in n_rfb or n_rfb in n_csv:
        return "⚠️", "match parcial (substring)"
    if n_csv_ss and (n_csv_ss in n_rfb or n_rfb in n_csv_ss):
        return "⚠️", "match parcial (sem sufixo)"
    if n_rfb_ss and (n_csv in n_rfb_ss or n_rfb_ss in n_csv):
        return "⚠️", "match parcial (sem sufixo RFB)"

    # --- Stage 6: word intersection ---
    # Try multiple normalization combinations to find best overlap
    _candidates = []
    for label, src in [("len", n_csv_len), ("strict", n_csv_ss or n_csv)]:
        for rlabel, rsrc in [("len", n_rfb_len), ("strict", n_rfb_ss or n_rfb)]:
            pal_a = _strip_genericas(set(src.split())) if src else set()
            pal_b = _strip_genericas(set(rsrc.split())) if rsrc else set()
            if pal_a and pal_b:
                inter = pal_a & pal_b
                min_len = min(len(pal_a), len(pal_b))
                if min_len > 0:
                    _candidates.append((len(inter) / min_len, inter, min_len, pal_a, pal_b, label, rlabel))

    if _candidates:
        best_ratio, best_inter, best_min, pal_a, pal_b, _, _ = max(_candidates, key=lambda x: x[0])
        if best_ratio >= 0.4:
            return "⚠️", f"match parcial ({len(best_inter)}/{best_min} palavras)"
        if best_inter:
            # 6b: word-level substring
            for w1 in pal_a:
                for w2 in pal_b:
                    if len(w1) >= 4 and len(w2) >= 4 and (w1 in w2 or w2 in w1):
                        return "⚠️", f"match parcial (substring palavra: {w1}/{w2})"
            return "❌", f"poucas palavras ({len(best_inter)}/{best_min})"

    # --- Stage 7: acronym ---
    ref = n_csv_ss or n_csv
    if _is_acronym(ref, n_rfb):
        return "⚠️", "match parcial (sigla)"
    if _is_acronym(n_rfb, ref):
        return "⚠️", "match parcial (sigla RFB)"

    # --- Stage 8: without spaces ---
    if n_csv.replace(" ", "") == n_rfb.replace(" ", ""):
        return "⚠️", "match parcial (sem espacos)"

    # --- Stage 9: rename mapping ---
    n_csv_up = n_csv.upper()
    n_rfb_up = n_rfb.upper()
    for old, new in _RENAMES.items():
        if old.upper() in n_csv_up and new.upper() in n_rfb_up:
            return "⚠️", f"match parcial (renome: {old}->{new})"
        if new.upper() in n_csv_up and old.upper() in n_rfb_up:
            return "⚠️", f"match parcial (renome: {new}->{old})"

    return "❌", "sem correspondencia"


def _carregar_cvm_cia() -> dict[str, str]:
    """cnpj_completo -> razao_social (raw, sem normalizar)"""
    result = {}
    path = CVM_CIA_PATH
    if not path.exists():
        return result
    with open(path, newline="", encoding="iso-8859-1") as f:
        for row in csv.DictReader(f, delimiter=";"):
            cnpj = re.sub(r"\D", "", (row.get("CNPJ_CIA") or "").strip())
            nome = (row.get("DENOM_SOCIAL") or "").strip()
            if cnpj and nome:
                result[cnpj] = nome
    return result


def _carregar_cvm_fi() -> dict[str, str]:
    """cnpj_completo -> razao_social (raw, sem normalizar)"""
    result = {}
    path = CVM_FI_PATH
    if not path.exists():
        return result
    with open(path, newline="", encoding="iso-8859-1") as f:
        for row in csv.DictReader(f, delimiter=";"):
            cnpj = re.sub(r"\D", "", (row.get("CNPJ_FUNDO") or "").strip())
            nome = (row.get("DENOM_SOCIAL") or "").strip()
            if cnpj and nome:
                result[cnpj] = nome
    return result


def validar(relatorio: bool = True) -> list[dict]:
    """Valida CNPJs do consolidado contra RFB + CVM."""
    if not CONSOLIDADO_PATH.exists():
        print(f"ERRO: consolidado não encontrado: {CONSOLIDADO_PATH}")
        return []

    if not RFB_DB_PATH.exists():
        print(f"AVISO: RFB DB não encontrado: {RFB_DB_PATH}")
        conn = None
    else:
        conn = sqlite3.connect(str(RFB_DB_PATH))

    cvm_cia = _carregar_cvm_cia()
    cvm_fi = _carregar_cvm_fi()

    with open(CONSOLIDADO_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    cnpj_map: dict[str, list[dict]] = defaultdict(list)
    for _i, row in enumerate(rows):
        cnpj = re.sub(r"\D", "", (row.get("cnpj_emissor") or "").strip())
        if not cnpj:
            continue
        cnpj_map[cnpj].append(row)

    resultados = []
    stats = {"✅": 0, "⚠️": 0, "❌": 0, "❓": 0}

    for cnpj_completo, emissores in sorted(cnpj_map.items()):
        base = cnpj_completo[:8]
        razao_rfb: str | None = None
        razao_cvm: str | None = None

        if conn is not None:
            cur = conn.execute(
                "SELECT razao_social FROM empresas WHERE cnpj_base = ?",
                (base,),
            )
            row_rfb = cur.fetchone()
            if row_rfb:
                razao_rfb = row_rfb[0]

        if not razao_rfb:
            if cnpj_completo in cvm_cia:
                razao_cvm = cvm_cia[cnpj_completo]
            elif cnpj_completo in cvm_fi:
                razao_cvm = cvm_fi[cnpj_completo]

        nome_base = razao_rfb or razao_cvm or ""
        fonte = "RFB" if razao_rfb else ("CVM" if razao_cvm else "")

        for row_emissor in emissores:
            emissor = row_emissor.get("no_emissor_padronizado", "").strip()
            cnpj_fmt = row_emissor.get("cnpj_emissor", "").strip()

            if not nome_base:
                status = "❓"
                obs = "não encontrado na RFB nem CVM"
                stats["❓"] += 1
            else:
                status, obs = _comparar_nomes(emissor, nome_base)
                if fonte:
                    obs += f" ({fonte})"
                stats[status] += 1

            resultados.append(
                {
                    "emissor": emissor,
                    "cnpj": cnpj_fmt,
                    "razao_rfb": razao_rfb or "",
                    "razao_cvm": razao_cvm or "",
                    "status": status,
                    "obs": obs,
                }
            )

    if conn is not None:
        conn.close()

    if relatorio:
        fieldnames = ["emissor", "cnpj", "razao_rfb", "razao_cvm", "status", "obs"]
        with open(RELATORIO_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(resultados)
        print(f"Relatório salvo: {RELATORIO_PATH}")

    total = sum(stats.values())
    print()
    print("=" * 60)
    print("  VALIDAÇÃO DE CNPJs — SUMÁRIO")
    print("=" * 60)
    print(f"  Total CNPJs únicos verificados: {len(cnpj_map)}")
    print(f"  Total emissores verificados:    {total}")
    print()
    print(f"  ✅ Match exato:     {stats['✅']:4d}  ({100 * stats['✅'] / total:.1f}%)" if total else "")
    print(f"  ⚠️  Match parcial:   {stats['⚠️']:4d}  ({100 * stats['⚠️'] / total:.1f}%)" if total else "")
    print(f"  ❌ Mismatch:         {stats['❌']:4d}  ({100 * stats['❌'] / total:.1f}%)" if total else "")
    print(f"  ❓ Não encontrado:   {stats['❓']:4d}  ({100 * stats['❓'] / total:.1f}%)" if total else "")
    print("=" * 60)

    mismatches = [r for r in resultados if r["status"] == "❌"]
    if mismatches:
        print()
        print("  ❌  PENDENTES DE VALIDAÇÃO:")
        for r in mismatches:
            print(f"    ❌ {r['emissor']}")
            print(f"       CNPJ: {r['cnpj']}")
            if r["razao_rfb"]:
                print(f"       RFB:  {r['razao_rfb']}")
            if r["razao_cvm"]:
                print(f"       CVM:  {r['razao_cvm']}")
            print()

    not_founds = [r for r in resultados if r["status"] == "❓"]
    if not_founds:
        print("  ❓  NÃO ENCONTRADOS (CNPJ não existe na RFB/CVM):")
        for r in not_founds:
            print(f"    ❓ {r['emissor']} — {r['cnpj']}")
        print()

    return resultados


def main():
    logging.basicConfig(level=logging.WARNING)
    validar()


if __name__ == "__main__":
    main()
