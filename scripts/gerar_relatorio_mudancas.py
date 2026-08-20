#!/usr/bin/env python
"""
Módulo: Gerador de Relatório de Movimentações de Ratings
Detecta Upgrades, Downgrades, Novos Ratings, Alterações de Perspectiva e Retiradas
entre as capturas do histórico de emissores e emissões.
"""

import csv
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from utils.paths import get_data_dir

logger = logging.getLogger("relatorio_mudancas")

# Régua unificada de Ratings (quanto menor o score, maior a qualidade de crédito)
RATING_SCORES: dict[str, int] = {
    "AAA": 1,
    "AA+": 2,
    "AA": 3,
    "AA-": 4,
    "A+": 5,
    "A": 6,
    "A-": 7,
    "BBB+": 8,
    "BBB": 9,
    "BBB-": 10,
    "BB+": 11,
    "BB": 12,
    "BB-": 13,
    "B+": 14,
    "B": 15,
    "B-": 16,
    "CCC+": 17,
    "CCC": 18,
    "CCC-": 19,
    "CC": 20,
    "C": 21,
    "D": 22,
    "RD": 22,
    "SD": 22,
    # Qualidade de Gestão / Investimentos (MQ / QG)
    "QG1": 1,
    "MQ1": 1,
    "QG2+": 2,
    "MQ2+": 2,
    "QG2": 3,
    "MQ2": 3,
    "QG2-": 4,
    "MQ2-": 4,
    "QG3+": 5,
    "MQ3+": 5,
    "QG3": 6,
    "MQ3": 6,
    "QG3-": 7,
    "MQ3-": 7,
    "QG4": 8,
    "MQ4": 8,
    "QG5": 9,
    "MQ5": 9,
}


def normalizar_rating(rating_str: str | None) -> tuple[str, int | None]:
    """
    Normaliza a nota de rating de qualquer agência (ex: 'brAA+', 'AAA.br', 'AA-(bra)', 'QG2-')
    para sua representação base e score numérico na régua.
    """
    if not rating_str:
        return "", None

    raw = str(rating_str).strip()
    if raw in ("-", "N/A", "WR", "NR", "None", ""):
        return raw, None

    # Remove sufixos como (bra), (sf), (exp), .br, etc
    clean = re.sub(r"\s*\(.*?\)", "", raw).strip()
    clean = re.sub(r"\.br$", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"^br", "", clean, flags=re.IGNORECASE).strip()
    clean = clean.upper()

    score = RATING_SCORES.get(clean)
    if score is None:
        raw_upper = raw.upper().replace(".BR", "")
        score = RATING_SCORES.get(raw_upper)
        if score is not None:
            clean = raw_upper

    return clean if clean else raw, score


def normalizar_outlook(outlook_str: str | None) -> str:
    """Normaliza descrições de perspectiva/outlook."""
    if not outlook_str:
        return "Estável"
    val = str(outlook_str).strip()
    val_lower = val.lower()
    if any(k in val_lower for k in ("revis", "observ", "watch", "under review")):
        return "Em Observação"
    if any(k in val_lower for k in ("positiv", "positive")):
        return "Positiva"
    if any(k in val_lower for k in ("negativ", "negative")):
        return "Negativa"
    if any(k in val_lower for k in ("estável", "estavel", "stable")):
        return "Estável"
    if val in ("-", "N/A", "None", ""):
        return "Estável"
    return val


def make_key(row: dict[str, Any], key_fields: list[str]) -> str:
    """Gera chave única para o emissor ou emissão."""
    parts = []
    for f in key_fields:
        val = str(row.get(f) or "").strip().upper()
        if not val and f == "no_emissor_padronizado":
            val = str(row.get("no_emissor_original") or row.get("no_emissor") or "").strip().upper()
        parts.append(val)
    return " | ".join(parts)


def extrair_ratings_vigentes(
    df_rows: list[dict[str, Any]],
    key_fields: list[str],
    date_col: str = "dt_acao_rating",
) -> dict[str, dict[str, Any]]:
    """
    Para cada chave única (ex: agência + emissor + tipo/instrumento), seleciona o registro
    com a data de ação mais recente (rating ativo vigente).
    """
    def sort_key(r: dict[str, Any]) -> tuple[str, str]:
        d_acao = str(r.get(date_col) or r.get("dt_rating") or "").strip()
        d_cap = str(r.get("dt_captura") or "").strip()
        return (d_acao, d_cap)

    sorted_rows = sorted(df_rows, key=sort_key)
    vigentes: dict[str, dict[str, Any]] = {}
    for r in sorted_rows:
        k = make_key(r, key_fields)
        if not k.replace("|", "").strip():
            continue
        vigentes[k] = r
    return vigentes


def comparar_snapshots(
    df_rows_or_map_atual: list[dict[str, Any]] | dict[str, dict[str, Any]],
    tipo_dataset: str,
    key_fields: list[str],
    map_anterior_override: dict[str, dict[str, Any]] | None = None,
    dt_atual_override: str | None = None,
    dt_anterior_override: str | None = None,
) -> dict[str, Any]:
    """
    Compara o snapshot de ratings vigente contra o snapshot anterior.
    Gera listas de Upgrades, Downgrades, Novos, Mudanças de Outlook e Retirados.

    Suporta chamada legada com df_rows contendo 'dt_captura' ou chamada direta com mapas.
    """
    if isinstance(df_rows_or_map_atual, dict):
        map_atual = df_rows_or_map_atual
        map_anterior = map_anterior_override or {}
        dt_atual = dt_atual_override or datetime.now().strftime("%Y-%m-%d")
        dt_anterior = dt_anterior_override or "N/A"
    else:
        df_rows = df_rows_or_map_atual
        if map_anterior_override is not None:
            map_atual = extrair_ratings_vigentes(df_rows, key_fields)
            map_anterior = map_anterior_override
            dt_atual = dt_atual_override or datetime.now().strftime("%Y-%m-%d")
            dt_anterior = dt_anterior_override or "N/A"
        else:
            # Modo legado / histórico baseado em capturas presentes nas linhas
            capturas = sorted(
                {r["dt_captura"] for r in df_rows if r.get("dt_captura")},
                reverse=True,
            )
            if not capturas:
                return {
                    "tipo": tipo_dataset,
                    "dt_atual": None,
                    "dt_anterior": None,
                    "upgrades": [],
                    "downgrades": [],
                    "novos": [],
                    "outlooks": [],
                    "retirados": [],
                }

            dt_atual = dt_atual_override or capturas[0]
            dt_anterior = dt_anterior_override or (capturas[1] if len(capturas) > 1 else None)

            rows_atual = [r for r in df_rows if r.get("dt_captura") == dt_atual]
            rows_anterior = [r for r in df_rows if r.get("dt_captura") == dt_anterior] if dt_anterior else []

            map_atual = extrair_ratings_vigentes(rows_atual, key_fields)
            map_anterior = extrair_ratings_vigentes(rows_anterior, key_fields)

    upgrades = []
    downgrades = []
    novos = []
    outlooks = []
    retirados = []

    # 1. Compara itens da captura atual contra a anterior
    for key, curr in map_atual.items():
        curr_rating_raw = curr.get("de_rating_br") or ""
        curr_rating_base, curr_score = normalizar_rating(curr_rating_raw)
        curr_outlook = normalizar_outlook(curr.get("de_outlook"))
        emissor_nome = (
            curr.get("no_emissor_padronizado")
            or curr.get("no_emissor_original")
            or curr.get("no_emissor")
            or ""
        )
        agencia = curr.get("agencia") or "N/A"
        instrumento = curr.get("de_instrumento") or curr.get("no_tipo_rating") or "Emissor"
        link = curr.get("link") or ""

        base_info = {
            "agencia": agencia,
            "emissor": emissor_nome,
            "instrumento": instrumento,
            "dt_acao": curr.get("dt_acao_rating") or curr.get("dt_rating") or dt_atual,
            "link": link,
        }

        if key not in map_anterior:
            # Novo rating identificado
            novos.append(
                {
                    **base_info,
                    "rating_atual": curr_rating_raw,
                    "outlook_atual": curr_outlook,
                    "tipo_movimento": "NOVO",
                }
            )
        else:
            prev = map_anterior[key]
            prev_rating_raw = prev.get("de_rating_br") or ""
            prev_rating_base, prev_score = normalizar_rating(prev_rating_raw)
            prev_outlook = normalizar_outlook(prev.get("de_outlook"))

            # Mudança de nota na régua
            if curr_score is not None and prev_score is not None:
                if curr_score < prev_score:
                    # Score menor = rating melhor (Upgrade)
                    upgrades.append(
                        {
                            **base_info,
                            "rating_anterior": prev_rating_raw,
                            "rating_atual": curr_rating_raw,
                            "outlook_anterior": prev_outlook,
                            "outlook_atual": curr_outlook,
                            "tipo_movimento": "UPGRADE",
                        }
                    )
                elif curr_score > prev_score:
                    # Score maior = rating pior (Downgrade)
                    downgrades.append(
                        {
                            **base_info,
                            "rating_anterior": prev_rating_raw,
                            "rating_atual": curr_rating_raw,
                            "outlook_anterior": prev_outlook,
                            "outlook_atual": curr_outlook,
                            "tipo_movimento": "DOWNGRADE",
                        }
                    )
                elif curr_outlook != prev_outlook:
                    # Nota idêntica, mas outlook mudou
                    outlooks.append(
                        {
                            **base_info,
                            "rating_atual": curr_rating_raw,
                            "outlook_anterior": prev_outlook,
                            "outlook_atual": curr_outlook,
                            "tipo_movimento": "OUTLOOK",
                        }
                    )
            elif curr_rating_raw != prev_rating_raw:
                # Mudança de rating sem score numérico mapeado
                upgrades.append(
                    {
                        **base_info,
                        "rating_anterior": prev_rating_raw,
                        "rating_atual": curr_rating_raw,
                        "outlook_anterior": prev_outlook,
                        "outlook_atual": curr_outlook,
                        "tipo_movimento": "ALTERACAO",
                    }
                )
            elif curr_outlook != prev_outlook:
                outlooks.append(
                    {
                        **base_info,
                        "rating_atual": curr_rating_raw,
                        "outlook_anterior": prev_outlook,
                        "outlook_atual": curr_outlook,
                        "tipo_movimento": "OUTLOOK",
                    }
                )

    # 2. Itens que estavam no snapshot anterior e deixaram de constar
    for key, prev in map_anterior.items():
        if key not in map_atual:
            emissor_nome = (
                prev.get("no_emissor_padronizado")
                or prev.get("no_emissor_original")
                or prev.get("no_emissor")
                or ""
            )
            agencia = prev.get("agencia") or "N/A"
            instrumento = prev.get("de_instrumento") or prev.get("no_tipo_rating") or "Emissor"
            retirados.append(
                {
                    "agencia": agencia,
                    "emissor": emissor_nome,
                    "instrumento": instrumento,
                    "rating_anterior": prev.get("de_rating_br") or "",
                    "outlook_anterior": normalizar_outlook(prev.get("de_outlook")),
                    "dt_acao": prev.get("dt_acao_rating") or prev.get("dt_rating") or dt_anterior,
                    "link": prev.get("link") or "",
                    "tipo_movimento": "RETIRADO",
                }
            )

    return {
        "tipo": tipo_dataset,
        "dt_atual": dt_atual,
        "dt_anterior": dt_anterior,
        "upgrades": upgrades,
        "downgrades": downgrades,
        "novos": novos,
        "outlooks": outlooks,
        "retirados": retirados,
    }


def carregar_snapshot_anterior(
    snapshot_dir: Path,
    dt_atual: str,
    rows_emissores: list[dict[str, Any]],
    rows_emissoes: list[dict[str, Any]],
    keys_emissores: list[str],
    keys_emissoes: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], str]:
    """
    Carrega o snapshot de ratings anterior a dt_atual.
    Se não houver snapshot gravado em disco (cold start / primeira execução),
    reconstrói a base anterior a partir do histórico de ações ou inicializa baseline.
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    # Procura arquivos de snapshot no diretório
    snapshot_files = sorted(snapshot_dir.glob("snapshot_*.json"))
    valid_snapshots = []
    for sf in snapshot_files:
        if sf.name in ("snapshot_latest.json", "snapshot_previous.json"):
            continue
        m = re.match(r"^snapshot_(\d{4}-\d{2}-\d{2})\.json$", sf.name)
        if m:
            s_date = m.group(1)
            if s_date < dt_atual:
                valid_snapshots.append((s_date, sf))

    if valid_snapshots:
        # Pega o snapshot mais recente anterior a dt_atual
        prev_date, prev_path = valid_snapshots[-1]
        try:
            with open(prev_path, encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Snapshot anterior carregado de {prev_path.name} ({prev_date})")
                return data.get("emissores", {}), data.get("emissoes", {}), prev_date
        except Exception as e:
            logger.warning(f"Falha ao ler snapshot {prev_path}: {e}")

    # Verifica se existe snapshot_previous.json
    prev_file = snapshot_dir / "snapshot_previous.json"
    if prev_file.exists():
        try:
            with open(prev_file, encoding="utf-8") as f:
                data = json.load(f)
                prev_date = data.get("dt_captura", "anterior")
                if prev_date != dt_atual:
                    logger.info(f"Snapshot anterior carregado de snapshot_previous.json ({prev_date})")
                    return data.get("emissores", {}), data.get("emissoes", {}), prev_date
        except Exception as e:
            logger.warning(f"Falha ao ler snapshot_previous.json: {e}")

    # Baseline inteligente: Se não há snapshot gravado, reconstrói o estado prévio
    # a partir das ações históricas registradas nos CSVs.
    logger.info("Nenhum snapshot anterior em disco. Reconstruindo baseline histórico a partir dos CSVs...")

    def reconstruir_baseline(rows: list[dict[str, Any]], key_fields: list[str]) -> dict[str, dict[str, Any]]:
        from collections import defaultdict

        acoes_por_chave = defaultdict(list)
        for r in rows:
            k = make_key(r, key_fields)
            if k.replace("|", "").strip():
                acoes_por_chave[k].append(r)

        baseline = {}
        for k, acoes in acoes_por_chave.items():
            def s_key(r):
                return (str(r.get("dt_acao_rating") or r.get("dt_rating") or ""), str(r.get("dt_captura") or ""))

            sorted_acoes = sorted(acoes, key=s_key)

            if len(sorted_acoes) > 1:
                ultima = sorted_acoes[-1]
                d_ultima = str(ultima.get("dt_acao_rating") or ultima.get("dt_rating") or ultima.get("dt_captura") or "")
                if d_ultima >= dt_atual:
                    baseline[k] = sorted_acoes[-2]
                else:
                    baseline[k] = ultima
            else:
                unica = sorted_acoes[0]
                d_unica = str(unica.get("dt_acao_rating") or unica.get("dt_rating") or "")
                if d_unica < dt_atual:
                    baseline[k] = unica

        return baseline

    prev_emissores = reconstruir_baseline(rows_emissores, keys_emissores)
    prev_emissoes = reconstruir_baseline(rows_emissoes, keys_emissoes)
    return prev_emissores, prev_emissoes, "baseline_inicial"


def salvar_snapshots(
    snapshot_dir: Path,
    dt_atual: str,
    vigentes_emissores: dict[str, dict[str, Any]],
    vigentes_emissoes: dict[str, dict[str, Any]],
) -> None:
    """Persiste o snapshot atual em arquivo diário e snapshot_latest.json."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "dt_captura": dt_atual,
        "timestamp": datetime.now().isoformat(),
        "total_emissores": len(vigentes_emissores),
        "total_emissoes": len(vigentes_emissoes),
        "emissores": vigentes_emissores,
        "emissoes": vigentes_emissoes,
    }

    # Salva snapshot diário
    daily_file = snapshot_dir / f"snapshot_{dt_atual}.json"
    with open(daily_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Se snapshot_latest já existia e tinha data diferente de dt_atual, salva como snapshot_previous
    latest_file = snapshot_dir / "snapshot_latest.json"
    if latest_file.exists():
        try:
            with open(latest_file, encoding="utf-8") as f:
                old_data = json.load(f)
            if old_data.get("dt_captura") != dt_atual:
                with open(snapshot_dir / "snapshot_previous.json", "w", encoding="utf-8") as pf:
                    json.dump(old_data, pf, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Aviso ao arquivar snapshot_previous: {e}")

    # Atualiza snapshot_latest.json
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Snapshots salvos com sucesso em {snapshot_dir}")


def gerar_markdown(relatorio: dict[str, Any]) -> str:
    """Gera relatório legível em Markdown formatado com tabelas e ícones."""
    dt_atual = relatorio.get("dt_atual", datetime.now().strftime("%Y-%m-%d"))
    dt_ant = relatorio.get("dt_anterior", "N/A")

    md = [
        f"# 📊 Relatório de Movimentações de Ratings ({dt_atual})",
        f"\n*Comparativo entre a captura de **{dt_atual}** e a captura anterior de **{dt_ant}**.*\n",
    ]

    resumo = relatorio.get("resumo", {})
    md.append("### 📈 Resumo Geral das Alterações")
    md.append("| Categoria | Emissores | Emissões | Total |")
    md.append("| :--- | :---: | :---: | :---: |")
    md.append(
        f"| 🟢 **Upgrades (Elevações)** | {resumo.get('upgrades_emissores', 0)} | {resumo.get('upgrades_emissoes', 0)} | **{resumo.get('total_upgrades', 0)}** |"
    )
    md.append(
        f"| 🔴 **Downgrades (Rebaixamentos)** | {resumo.get('downgrades_emissores', 0)} | {resumo.get('downgrades_emissoes', 0)} | **{resumo.get('total_downgrades', 0)}** |"
    )
    md.append(
        f"| 🔵 **Novos Ratings** | {resumo.get('novos_emissores', 0)} | {resumo.get('novos_emissoes', 0)} | **{resumo.get('total_novos', 0)}** |"
    )
    md.append(
        f"| 🟡 **Mudanças de Perspectiva** | {resumo.get('outlooks_emissores', 0)} | {resumo.get('outlooks_emissoes', 0)} | **{resumo.get('total_outlooks', 0)}** |"
    )
    md.append(
        f"| ⚪ **Ratings Retirados** | {resumo.get('retirados_emissores', 0)} | {resumo.get('retirados_emissoes', 0)} | **{resumo.get('total_retirados', 0)}** |"
    )
    md.append("")

    all_upgrades = relatorio.get("emissores", {}).get("upgrades", []) + relatorio.get("emissoes", {}).get(
        "upgrades", []
    )
    if all_upgrades:
        md.append("### 🟢 Elevações de Rating (Upgrades)")
        md.append(
            "| Agência | Emissor | Instrumento / Tipo | Anterior | Novo Rating | Perspectiva | Data Ação |"
        )
        md.append("| :--- | :--- | :--- | :---: | :---: | :--- | :---: |")
        for u in all_upgrades:
            md.append(
                f"| {u['agencia']} | **{u['emissor']}** | {u['instrumento']} | `{u['rating_anterior']}` | **`{u['rating_atual']}`** | {u['outlook_atual']} | {u['dt_acao']} |"
            )
        md.append("")

    all_downgrades = relatorio.get("emissores", {}).get("downgrades", []) + relatorio.get("emissoes", {}).get(
        "downgrades", []
    )
    if all_downgrades:
        md.append("### 🔴 Rebaixamentos de Rating (Downgrades)")
        md.append(
            "| Agência | Emissor | Instrumento / Tipo | Anterior | Novo Rating | Perspectiva | Data Ação |"
        )
        md.append("| :--- | :--- | :--- | :---: | :---: | :--- | :---: |")
        for d in all_downgrades:
            md.append(
                f"| {d['agencia']} | **{d['emissor']}** | {d['instrumento']} | `{d['rating_anterior']}` | **`{d['rating_atual']}`** | {d['outlook_atual']} | {d['dt_acao']} |"
            )
        md.append("")

    all_outlooks = relatorio.get("emissores", {}).get("outlooks", []) + relatorio.get("emissoes", {}).get(
        "outlooks", []
    )
    if all_outlooks:
        md.append("### 🟡 Mudanças de Perspectiva (Outlook)")
        md.append(
            "| Agência | Emissor | Instrumento / Tipo | Rating | Perspectiva Anterior | Nova Perspectiva | Data Ação |"
        )
        md.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: |")
        for o in all_outlooks:
            md.append(
                f"| {o['agencia']} | **{o['emissor']}** | {o['instrumento']} | `{o['rating_atual']}` | {o['outlook_anterior']} | **{o['outlook_atual']}** | {o['dt_acao']} |"
            )
        md.append("")

    all_novos = relatorio.get("emissores", {}).get("novos", []) + relatorio.get("emissoes", {}).get(
        "novos", []
    )
    if all_novos:
        md.append(f"### 🔵 Novos Ratings Adicionados ({len(all_novos)})")
        md.append("| Agência | Emissor | Instrumento / Tipo | Rating | Perspectiva | Data Ação |")
        md.append("| :--- | :--- | :--- | :---: | :--- | :---: |")
        for n in all_novos[:30]:
            md.append(
                f"| {n['agencia']} | **{n['emissor']}** | {n['instrumento']} | **`{n['rating_atual']}`** | {n['outlook_atual']} | {n['dt_acao']} |"
            )
        if len(all_novos) > 30:
            md.append(f"| *...e mais {len(all_novos) - 30} novos ratings.* | | | | | |")
        md.append("")

    all_retirados = relatorio.get("emissores", {}).get("retirados", []) + relatorio.get("emissoes", {}).get(
        "retirados", []
    )
    if all_retirados:
        md.append(f"### ⚪ Ratings Retirados / Descontinuados ({len(all_retirados)})")
        md.append("| Agência | Emissor | Instrumento / Tipo | Último Rating | Perspectiva | Data |")
        md.append("| :--- | :--- | :--- | :---: | :--- | :---: |")
        for r in all_retirados[:30]:
            md.append(
                f"| {r['agencia']} | **{r['emissor']}** | {r['instrumento']} | `{r['rating_anterior']}` | {r['outlook_anterior']} | {r['dt_acao']} |"
            )
        if len(all_retirados) > 30:
            md.append(f"| *...e mais {len(all_retirados) - 30} ratings retirados.* | | | | | |")
        md.append("")

    if not all_upgrades and not all_downgrades and not all_outlooks and not all_novos and not all_retirados:
        md.append("> *Nenhuma movimentação de rating detectada entre as capturas comparadas.*")

    return "\n".join(md)


def generate() -> dict[str, Any]:
    """Executa a análise completa de movimentações e salva os relatórios."""
    data_dir = get_data_dir()
    snapshot_dir = data_dir / "snapshots"
    path_emissores = data_dir / "ratings_emissores.csv"
    path_emissoes = data_dir / "ratings_emissoes.csv"

    rows_emissores: list[dict[str, Any]] = []
    if path_emissores.exists():
        with open(path_emissores, encoding="utf-8") as f:
            rows_emissores = list(csv.DictReader(f))

    rows_emissoes: list[dict[str, Any]] = []
    if path_emissoes.exists():
        with open(path_emissoes, encoding="utf-8") as f:
            rows_emissoes = list(csv.DictReader(f))

    keys_emissores = ["agencia", "no_emissor_padronizado", "no_tipo_rating"]
    keys_emissoes = ["agencia", "no_emissor_padronizado", "de_instrumento"]

    # Extrai o universo de ratings vigentes ativos
    vigentes_emissores = extrair_ratings_vigentes(rows_emissores, keys_emissores)
    vigentes_emissoes = extrair_ratings_vigentes(rows_emissoes, keys_emissoes)

    # Identifica data atual
    todas_capturas = {r["dt_captura"] for r in (rows_emissores + rows_emissoes) if r.get("dt_captura")}
    dt_atual = max(todas_capturas) if todas_capturas else datetime.now().strftime("%Y-%m-%d")

    # Carrega snapshot anterior para comparação
    prev_emissores, prev_emissoes, dt_anterior = carregar_snapshot_anterior(
        snapshot_dir=snapshot_dir,
        dt_atual=dt_atual,
        rows_emissores=rows_emissores,
        rows_emissoes=rows_emissoes,
        keys_emissores=keys_emissores,
        keys_emissoes=keys_emissoes,
    )

    logger.info("Comparando movimentações de ratings de emissores...")
    diff_emissores = comparar_snapshots(
        df_rows_or_map_atual=vigentes_emissores,
        tipo_dataset="emissores",
        key_fields=keys_emissores,
        map_anterior_override=prev_emissores,
        dt_atual_override=dt_atual,
        dt_anterior_override=dt_anterior,
    )

    logger.info("Comparando movimentações de ratings de emissões...")
    diff_emissoes = comparar_snapshots(
        df_rows_or_map_atual=vigentes_emissoes,
        tipo_dataset="emissoes",
        key_fields=keys_emissoes,
        map_anterior_override=prev_emissoes,
        dt_atual_override=dt_atual,
        dt_anterior_override=dt_anterior,
    )

    resumo = {
        "upgrades_emissores": len(diff_emissores["upgrades"]),
        "upgrades_emissoes": len(diff_emissoes["upgrades"]),
        "total_upgrades": len(diff_emissores["upgrades"]) + len(diff_emissoes["upgrades"]),
        "downgrades_emissores": len(diff_emissores["downgrades"]),
        "downgrades_emissoes": len(diff_emissoes["downgrades"]),
        "total_downgrades": len(diff_emissores["downgrades"]) + len(diff_emissoes["downgrades"]),
        "novos_emissores": len(diff_emissores["novos"]),
        "novos_emissoes": len(diff_emissoes["novos"]),
        "total_novos": len(diff_emissores["novos"]) + len(diff_emissoes["novos"]),
        "outlooks_emissores": len(diff_emissores["outlooks"]),
        "outlooks_emissoes": len(diff_emissoes["outlooks"]),
        "total_outlooks": len(diff_emissores["outlooks"]) + len(diff_emissoes["outlooks"]),
        "retirados_emissores": len(diff_emissores["retirados"]),
        "retirados_emissoes": len(diff_emissoes["retirados"]),
        "total_retirados": len(diff_emissores["retirados"]) + len(diff_emissoes["retirados"]),
    }

    relatorio = {
        "timestamp": datetime.now().isoformat(),
        "dt_atual": dt_atual,
        "dt_anterior": dt_anterior,
        "resumo": resumo,
        "emissores": diff_emissores,
        "emissoes": diff_emissoes,
    }

    # Salva JSON
    json_path = data_dir / "movimentacoes_ratings.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    logger.info(f"Relatório JSON salvo em {json_path}")

    # Salva JS
    js_path = data_dir / "movimentacoes_ratings.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(
            f"window.PULSERATINGS_MOVIMENTACOES = {json.dumps(relatorio, indent=2, ensure_ascii=False)};\n"
        )
    logger.info(f"Relatório JS salvo em {js_path}")

    # Salva Markdown
    md_content = gerar_markdown(relatorio)
    md_path = data_dir / "movimentacoes_ratings.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"Relatório Markdown salvo em {md_path}")

    # Persiste snapshots para a próxima rodada
    salvar_snapshots(
        snapshot_dir=snapshot_dir,
        dt_atual=dt_atual,
        vigentes_emissores=vigentes_emissores,
        vigentes_emissoes=vigentes_emissoes,
    )

    return relatorio


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rel = generate()
    print(f"\nResumo de Movimentações ({rel['dt_atual']} vs {rel['dt_anterior']}):")
    print(f"  🟢 Upgrades:    {rel['resumo']['total_upgrades']}")
    print(f"  🔴 Downgrades:  {rel['resumo']['total_downgrades']}")
    print(f"  🔵 Novos:       {rel['resumo']['total_novos']}")
    print(f"  🟡 Outlooks:    {rel['resumo']['total_outlooks']}")
    print(f"  ⚪ Retirados:   {rel['resumo']['total_retirados']}")
