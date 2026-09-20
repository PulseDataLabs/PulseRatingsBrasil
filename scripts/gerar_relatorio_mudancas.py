#!/usr/bin/env python
"""
Módulo: Gerador de Relatório de Movimentações de Ratings
Detecta Upgrades, Downgrades, Novos Ratings, Alterações de Perspectiva e Retiradas
entre as capturas do histórico de emissores e emissões (período recente de 30 dias e diário).
Mantém base histórica cumulativa em data/historico_movimentacoes.csv e relatórios arquivados.
"""

import csv
import json
import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from utils.paths import get_data_dir

logger = logging.getLogger("relatorio_mudancas")

# Régua unificada de Ratings (quanto menor o score, maior a qualidade de crédito)
RATING_SCORES: dict[str, int] = {
    # Escalas de Longo Prazo Nacional e Global
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
    # Escalas de Curto Prazo (Fitch F1+..F3, S&P brA-1+..brA-3, Moody's ML A-1..ML B, Liberum CP1..CP5)
    "F1+": 1,
    "A-1+": 1,
    "CP1": 1,
    "ML A-1": 1,
    "F1": 2,
    "A-1": 2,
    "CP2": 2,
    "F2": 3,
    "A-2": 3,
    "CP3": 3,
    "ML A-2": 3,
    "F3": 4,
    "A-3": 4,
    "CP4": 4,
    "ML A-3": 4,
    "CP5": 5,
    "ML B": 5,
    "ML C": 6,
    # Qualidade de Gestão / Investimentos (MQ / QG / AMP)
    "QG1": 1, "MQ1": 1, "AMP1": 1,
    "QG2+": 2, "MQ2+": 2,
    "QG2": 3, "MQ2": 3, "AMP2": 3,
    "QG2-": 4, "MQ2-": 4,
    "QG3+": 5, "MQ3+": 5,
    "QG3": 6, "MQ3": 6, "AMP3": 6,
    "QG3-": 7, "MQ3-": 7,
    "QG4": 8, "MQ4": 8,
    "QG5": 9, "MQ5": 9,
}

NON_RATINGS = {
    "-", "N/A", "WR", "NR", "WD", "PIF", "NONE", "", "NULL",
    "SUSPENSO", "CANCELADO", "DESCONTINUADO", "RETIRADO"
}


def normalizar_rating(rating_str: str | None) -> tuple[str, int | None]:
    """
    Normaliza a nota de rating de qualquer agência (ex: 'brAA+', 'AAA.br', 'AA-(bra)', 'AA-sf(bra)', 'QG2-')
    para sua representação base e score numérico na régua.
    """
    if not rating_str:
        return "", None

    raw = str(rating_str).strip()
    raw_upper = raw.upper()
    if raw_upper in NON_RATINGS or any(raw_upper.startswith(p) for p in ("WD", "PIF", "WR", "NR")):
        clean_status = re.sub(r"\s*\([^)]*\)", "", raw_upper).strip()
        return clean_status if clean_status else raw_upper, None

    # Remove parênteses como (bra), (sf), (exp), (fe), etc
    clean = re.sub(r"\s*\([^)]*\)", "", raw).strip()
    clean = re.sub(r"\.br$", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"^br", "", clean, flags=re.IGNORECASE).strip()

    # Remove sufixos de structured finance ou indicativos anexados à nota (ex: AA-sf -> AA-, BBBsf -> BBB, Csf -> C)
    clean = re.sub(r"(?<=[A-Za-z0-9\+\-])(sf|f)$", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"(?<=[A-Za-z0-9\+\-])exp$", "", clean, flags=re.IGNORECASE).strip()
    clean = clean.upper()

    score = RATING_SCORES.get(clean)
    if score is None:
        alt = clean.replace(".BR", "").replace("-", "").strip()
        score = RATING_SCORES.get(alt)

    return clean if clean else raw, score


def calcular_variacao_notches(r_ant: str | None, r_atu: str | None) -> str:
    """Calcula a variação em degraus (notches) entre a nota anterior e a nova."""
    _, s_ant = normalizar_rating(r_ant)
    _, s_atu = normalizar_rating(r_atu)
    if s_ant is not None and s_atu is not None:
        diff = s_ant - s_atu
        return f"+{diff}" if diff > 0 else str(diff)
    return "—"


def formatar_data_br(raw_date: str | None) -> str:
    """Converte data de YYYY-MM-DD para DD/MM/YYYY."""
    if not raw_date or raw_date in ("—", "N/A", "None", ""):
        return "—"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(raw_date).strip())
    if m:
        y, mo, d = m.groups()
        return f"{d}/{mo}/{y}"
    return str(raw_date)


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
    if val.upper() in NON_RATINGS:
        return "Estável"
    return val


def make_key(row: dict[str, Any], key_fields: list[str]) -> str:
    """Gera chave única para o emissor ou emissão."""
    parts = []
    for f in key_fields:
        val = str(row.get(f) or "").strip().upper()
        if not val and f == "no_emissor_padronizado":
            val = str(row.get("no_emissor_original") or row.get("no_emissor") or "").strip().upper()
        if not val and f == "de_instrumento":
            val = str(row.get("no_emissor_original") or row.get("no_tipo_rating") or "").strip().upper()
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

        curr_dt_acao = str(curr.get("dt_acao_rating") or curr.get("dt_rating") or "")

        if key not in map_anterior:
            # Só é considerado "NOVO RATING" no relatório se a ação de rating ocorreu no período monitorado
            if dt_anterior and curr_dt_acao and curr_dt_acao < dt_anterior:
                pass  # Registro legado / carga histórica anterior, não é concessão nova no período
            elif curr_score is not None:
                novos.append(
                    {
                        **base_info,
                        "rating_atual": curr_rating_raw,
                        "outlook_atual": curr_outlook,
                        "tipo_movimento": "NOVO",
                        "variacao_notches": "—",
                    }
                )
        else:
            prev = map_anterior[key]
            prev_rating_raw = prev.get("de_rating_br") or ""
            prev_rating_base, prev_score = normalizar_rating(prev_rating_raw)
            prev_outlook = normalizar_outlook(prev.get("de_outlook"))

            notches = calcular_variacao_notches(prev_rating_raw, curr_rating_raw)

            if curr_score is not None and prev_score is not None:
                if curr_score < prev_score:
                    upgrades.append(
                        {
                            **base_info,
                            "rating_anterior": prev_rating_raw,
                            "rating_atual": curr_rating_raw,
                            "outlook_anterior": prev_outlook,
                            "outlook_atual": curr_outlook,
                            "tipo_movimento": "UPGRADE",
                            "variacao_notches": notches,
                        }
                    )
                elif curr_score > prev_score:
                    downgrades.append(
                        {
                            **base_info,
                            "rating_anterior": prev_rating_raw,
                            "rating_atual": curr_rating_raw,
                            "outlook_anterior": prev_outlook,
                            "outlook_atual": curr_outlook,
                            "tipo_movimento": "DOWNGRADE",
                            "variacao_notches": notches,
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
                            "variacao_notches": "0",
                        }
                    )
            elif prev_score is not None and (curr_score is None or curr_rating_base in NON_RATINGS):
                retirados.append(
                    {
                        **base_info,
                        "rating_anterior": prev_rating_raw,
                        "rating_atual": curr_rating_raw,
                        "outlook_anterior": prev_outlook,
                        "outlook_atual": curr_outlook,
                        "tipo_movimento": "RETIRADO",
                        "variacao_notches": "—",
                    }
                )
            elif prev_score is None and curr_score is not None:
                if dt_anterior and curr_dt_acao and curr_dt_acao < dt_anterior:
                    pass
                else:
                    novos.append(
                        {
                            **base_info,
                            "rating_anterior": prev_rating_raw,
                            "rating_atual": curr_rating_raw,
                            "outlook_anterior": prev_outlook,
                            "outlook_atual": curr_outlook,
                            "tipo_movimento": "NOVO",
                            "variacao_notches": "—",
                        }
                    )

    for key, prev in map_anterior.items():
        if key not in map_atual:
            p_raw = prev.get("de_rating_br") or ""
            _, p_score = normalizar_rating(p_raw)
            if p_score is None:
                continue
            
            # Só reporta como retirado no período se o registro tinha data recente consistente com o período
            p_dt = str(prev.get("dt_acao_rating") or prev.get("dt_rating") or "")
            if dt_anterior and p_dt and p_dt < dt_anterior:
                # Discrepâncias de chaves legadas ou itens antigos sem movimentação não são retiradas ativas no período
                continue

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
                    "rating_anterior": p_raw,
                    "rating_atual": "RETIRADO",
                    "outlook_anterior": normalizar_outlook(prev.get("de_outlook")),
                    "dt_acao": prev.get("dt_acao_rating") or prev.get("dt_rating") or dt_anterior,
                    "link": prev.get("link") or "",
                    "tipo_movimento": "RETIRADO",
                    "variacao_notches": "—",
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


def carregar_snapshots_historicos(
    snapshot_dir: Path,
    dt_atual: str,
) -> tuple[dict[str, dict[str, Any]], str, dict[str, dict[str, Any]], str]:
    """
    Carrega o snapshot anterior diário (D-1) E o snapshot do período de 30 dias (ou mais antigo disponível).
    Retorna: (snap_diario, dt_diario, snap_periodo_30d, dt_periodo_30d)
    """
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

    snap_diario = {"emissores": {}, "emissoes": {}}
    dt_diario = "N/A"
    snap_periodo = {"emissores": {}, "emissoes": {}}
    dt_periodo = "N/A"

    if valid_snapshots:
        dt_diario, path_diario = valid_snapshots[-1]
        try:
            with open(path_diario, encoding="utf-8") as f:
                snap_diario = json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao ler snapshot diário {path_diario}: {e}")

        dt_alvo_30d = (datetime.strptime(dt_atual, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        snap_30d_candidates = [s for s in valid_snapshots if s[0] <= dt_alvo_30d]
        if snap_30d_candidates:
            dt_periodo, path_periodo = snap_30d_candidates[-1]
        else:
            dt_periodo, path_periodo = valid_snapshots[0]

        try:
            with open(path_periodo, encoding="utf-8") as f:
                snap_periodo = json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao ler snapshot do período {path_periodo}: {e}")

    return (
        snap_diario,
        dt_diario,
        snap_periodo,
        dt_periodo,
    )


def carregar_snapshot_anterior(
    snapshot_dir: Path,
    dt_atual: str,
    rows_emissores: list[dict[str, Any]],
    rows_emissoes: list[dict[str, Any]],
    keys_emissores: list[str],
    keys_emissoes: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], str]:
    """Função de compatibilidade com chamadas legadas/testes."""
    snap_diario, dt_diario, _, _ = carregar_snapshots_historicos(snapshot_dir, dt_atual)
    if snap_diario.get("emissores") or snap_diario.get("emissoes"):
        return snap_diario.get("emissores", {}), snap_diario.get("emissoes", {}), dt_diario
    return {}, {}, "baseline_inicial"


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

    daily_file = snapshot_dir / f"snapshot_{dt_atual}.json"
    with open(daily_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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

    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Snapshots salvos com sucesso em {snapshot_dir}")


def salvar_historico_movimentacoes(data_dir: Path, novos_eventos: list[dict[str, Any]]) -> None:
    """
    Mantém tabela cumulativa e deduplicada com o histórico de todas as movimentações detectadas.
    """
    hist_file = data_dir / "historico_movimentacoes.csv"
    headers = [
        "dt_captura",
        "dt_acao_rating",
        "agencia",
        "categoria",
        "no_emissor_padronizado",
        "no_emissor_original",
        "de_instrumento",
        "no_tipo_rating",
        "tipo_movimento",
        "rating_anterior",
        "rating_atual",
        "variacao_notches",
        "outlook_anterior",
        "outlook_atual",
        "link",
    ]
    existentes = []
    if hist_file.exists():
        with open(hist_file, encoding="utf-8") as f:
            existentes = list(csv.DictReader(f))

    seen = {
        (
            r.get("dt_captura"),
            r.get("agencia"),
            r.get("categoria"),
            r.get("no_emissor_padronizado"),
            r.get("de_instrumento"),
            r.get("tipo_movimento"),
            r.get("rating_anterior"),
            r.get("rating_atual"),
        )
        for r in existentes
    }

    adicionados = 0
    for ev in novos_eventos:
        # Validação de integridade
        dt_act = str(ev.get("dt_acao_rating") or ev.get("dt_acao") or "")
        if dt_act and dt_act < "2026-01-01" and ev.get("tipo_movimento") in ("UPGRADE", "DOWNGRADE"):
            continue

        item_row = {
            "dt_captura": ev.get("dt_captura") or datetime.now().strftime("%Y-%m-%d"),
            "dt_acao_rating": dt_act or ev.get("dt_captura") or "",
            "agencia": ev.get("agencia") or "",
            "categoria": ev.get("categoria") or "Emissor",
            "no_emissor_padronizado": ev.get("no_emissor_padronizado") or ev.get("emissor") or "",
            "no_emissor_original": ev.get("no_emissor_original") or ev.get("emissor") or "",
            "de_instrumento": ev.get("de_instrumento") or ev.get("instrumento") or "",
            "no_tipo_rating": ev.get("no_tipo_rating") or ev.get("instrumento") or "",
            "tipo_movimento": ev.get("tipo_movimento") or "",
            "rating_anterior": ev.get("rating_anterior") or "",
            "rating_atual": ev.get("rating_atual") or "",
            "variacao_notches": ev.get("variacao_notches") or calcular_variacao_notches(ev.get("rating_anterior"), ev.get("rating_atual")),
            "outlook_anterior": ev.get("outlook_anterior") or "",
            "outlook_atual": ev.get("outlook_atual") or "",
            "link": ev.get("link") or "",
        }

        k = (
            item_row["dt_captura"],
            item_row["agencia"],
            item_row["categoria"],
            item_row["no_emissor_padronizado"],
            item_row["de_instrumento"],
            item_row["tipo_movimento"],
            item_row["rating_anterior"],
            item_row["rating_atual"],
        )
        if k not in seen:
            seen.add(k)
            existentes.append(item_row)
            adicionados += 1

    existentes.sort(key=lambda e: (str(e.get("dt_captura") or ""), str(e.get("dt_acao_rating") or "")), reverse=True)

    with open(hist_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(existentes)

    logger.info(f"Histórico cumulativo atualizado em {hist_file} (+{adicionados} novos registros, total {len(existentes)})")


def gerar_markdown(relatorio: dict[str, Any]) -> str:
    """Gera relatório legível em Markdown formatado com tabelas e datas no formato pt_BR (DD/MM/YYYY)."""
    dt_atual = relatorio.get("dt_atual", datetime.now().strftime("%Y-%m-%d"))
    periodo_info = relatorio.get("periodo_recente") or relatorio
    dt_inicio_periodo = periodo_info.get("dt_anterior", "Início do Monitoramento")
    resumo_periodo = periodo_info.get("resumo", {})

    dt_atual_br = formatar_data_br(dt_atual)
    dt_inicio_br = formatar_data_br(dt_inicio_periodo)

    md = [
        f"# 📊 Relatório de Movimentações de Ratings ({dt_atual_br})",
        f"\n*Painel consolidado de **Upgrades**, **Downgrades**, **Novos Ratings** e **Alterações de Perspectiva**.*",
        f"\n*Período monitorado: **{dt_inicio_br}** a **{dt_atual_br}**.*\n",
    ]

    md.append("### 📈 Resumo Geral do Período Monitorado")
    md.append("| Categoria | Emissores | Emissões | Total |")
    md.append("| :--- | :---: | :---: | :---: |")
    md.append(
        f"| 🟢 **Upgrades (Elevações)** | {resumo_periodo.get('upgrades_emissores', 0)} | {resumo_periodo.get('upgrades_emissoes', 0)} | **{resumo_periodo.get('total_upgrades', 0)}** |"
    )
    md.append(
        f"| 🔴 **Downgrades (Rebaixamentos)** | {resumo_periodo.get('downgrades_emissores', 0)} | {resumo_periodo.get('downgrades_emissoes', 0)} | **{resumo_periodo.get('total_downgrades', 0)}** |"
    )
    md.append(
        f"| 🔵 **Novos Ratings** | {resumo_periodo.get('novos_emissores', 0)} | {resumo_periodo.get('novos_emissoes', 0)} | **{resumo_periodo.get('total_novos', 0)}** |"
    )
    md.append(
        f"| 🟡 **Mudanças de Perspectiva** | {resumo_periodo.get('outlooks_emissores', 0)} | {resumo_periodo.get('outlooks_emissoes', 0)} | **{resumo_periodo.get('total_outlooks', 0)}** |"
    )
    md.append(
        f"| ⚪ **Ratings Retirados / Liquidados** | {resumo_periodo.get('retirados_emissores', 0)} | {resumo_periodo.get('retirados_emissoes', 0)} | **{resumo_periodo.get('total_retirados', 0)}** |"
    )
    md.append("")

    all_upgrades = periodo_info.get("emissores", {}).get("upgrades", []) + periodo_info.get("emissoes", {}).get("upgrades", [])
    if all_upgrades:
        md.append(f"### 🟢 Elevações de Rating (Upgrades) — {len(all_upgrades)}")
        md.append(
            "| Agência | Emissor | Instrumento / Tipo | Anterior | Novo Rating | Variação | Perspectiva | Data Ação |"
        )
        md.append("| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |")
        for u in all_upgrades:
            dt_br = formatar_data_br(u.get("dt_acao"))
            notches = u.get("variacao_notches") or calcular_variacao_notches(u.get("rating_anterior"), u.get("rating_atual"))
            md.append(
                f"| {u['agencia']} | **{u['emissor']}** | {u['instrumento']} | `{u['rating_anterior']}` | **`{u['rating_atual']}`** | `{notches}` | {u['outlook_atual']} | {dt_br} |"
            )
        md.append("")

    all_downgrades = periodo_info.get("emissores", {}).get("downgrades", []) + periodo_info.get("emissoes", {}).get("downgrades", [])
    if all_downgrades:
        md.append(f"### 🔴 Rebaixamentos de Rating (Downgrades) — {len(all_downgrades)}")
        md.append(
            "| Agência | Emissor | Instrumento / Tipo | Anterior | Novo Rating | Variação | Perspectiva | Data Ação |"
        )
        md.append("| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |")
        for d in all_downgrades:
            dt_br = formatar_data_br(d.get("dt_acao"))
            notches = d.get("variacao_notches") or calcular_variacao_notches(d.get("rating_anterior"), d.get("rating_atual"))
            md.append(
                f"| {d['agencia']} | **{d['emissor']}** | {d['instrumento']} | `{d['rating_anterior']}` | **`{d['rating_atual']}`** | `{notches}` | {d['outlook_atual']} | {dt_br} |"
            )
        md.append("")

    all_outlooks = periodo_info.get("emissores", {}).get("outlooks", []) + periodo_info.get("emissoes", {}).get("outlooks", [])
    if all_outlooks:
        md.append(f"### 🟡 Mudanças de Perspectiva (Outlook) — {len(all_outlooks)}")
        md.append(
            "| Agência | Emissor | Instrumento / Tipo | Rating | Perspectiva Anterior | Nova Perspectiva | Data Ação |"
        )
        md.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: |")
        for o in all_outlooks:
            dt_br = formatar_data_br(o.get("dt_acao"))
            md.append(
                f"| {o['agencia']} | **{o['emissor']}** | {o['instrumento']} | `{o['rating_atual']}` | {o['outlook_anterior']} | **{o['outlook_atual']}** | {dt_br} |"
            )
        md.append("")

    all_novos = periodo_info.get("emissores", {}).get("novos", []) + periodo_info.get("emissoes", {}).get("novos", [])
    if all_novos:
        md.append(f"### 🔵 Novos Ratings Atribuídos ({len(all_novos)})")
        md.append("| Agência | Emissor | Instrumento / Tipo | Rating | Perspectiva | Data Ação |")
        md.append("| :--- | :--- | :--- | :---: | :--- | :---: |")
        for n in all_novos[:30]:
            dt_br = formatar_data_br(n.get("dt_acao"))
            md.append(
                f"| {n['agencia']} | **{n['emissor']}** | {n['instrumento']} | **`{n['rating_atual']}`** | {n['outlook_atual']} | {dt_br} |"
            )
        if len(all_novos) > 30:
            md.append(f"| *...e mais {len(all_novos) - 30} novos ratings.* | | | | | |")
        md.append("")

    all_retirados = periodo_info.get("emissores", {}).get("retirados", []) + periodo_info.get("emissoes", {}).get("retirados", [])
    if all_retirados:
        md.append(f"### ⚪ Ratings Retirados / Liquidados ({len(all_retirados)})")
        md.append("| Agência | Emissor | Instrumento / Tipo | Último Rating | Perspectiva | Data |")
        md.append("| :--- | :--- | :--- | :---: | :--- | :---: |")
        for r in all_retirados[:30]:
            dt_br = formatar_data_br(r.get("dt_acao"))
            md.append(
                f"| {r['agencia']} | **{r['emissor']}** | {r['instrumento']} | `{r['rating_anterior']}` | {r.get('outlook_anterior', 'Estável')} | {dt_br} |"
            )
        if len(all_retirados) > 30:
            md.append(f"| *...e mais {len(all_retirados) - 30} ratings retirados.* | | | | | |")
        md.append("")

    diario_info = relatorio.get("diario", {})
    res_diario = diario_info.get("resumo", {})
    dt_ant_diario_br = formatar_data_br(diario_info.get("dt_anterior", "D-1"))
    md.append("---")
    md.append(f"### ⚡ Movimentações da Última Captura Diária ({dt_ant_diario_br} → {dt_atual_br})")
    md.append(
        f"*Total nas últimas 24h: 🟢 {res_diario.get('total_upgrades', 0)} upgrades | "
        f"🔴 {res_diario.get('total_downgrades', 0)} downgrades | "
        f"🔵 {res_diario.get('total_novos', 0)} novos | "
        f"🟡 {res_diario.get('total_outlooks', 0)} perspectivas | "
        f"⚪ {res_diario.get('total_retirados', 0)} retirados.*"
    )

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

    vigentes_emissores = extrair_ratings_vigentes(rows_emissores, keys_emissores)
    vigentes_emissoes = extrair_ratings_vigentes(rows_emissoes, keys_emissoes)

    todas_capturas = {r["dt_captura"] for r in (rows_emissores + rows_emissoes) if r.get("dt_captura")}
    dt_atual = max(todas_capturas) if todas_capturas else datetime.now().strftime("%Y-%m-%d")

    snap_diario, dt_diario, snap_periodo, dt_periodo = carregar_snapshots_historicos(
        snapshot_dir=snapshot_dir,
        dt_atual=dt_atual,
    )

    # 1. Comparativo do Período Recente (30 dias / histórico monitorado)
    logger.info(f"Comparando movimentações do período monitorado ({dt_periodo} → {dt_atual})...")
    diff_periodo_emissores = comparar_snapshots(
        df_rows_or_map_atual=vigentes_emissores,
        tipo_dataset="emissores",
        key_fields=keys_emissores,
        map_anterior_override=snap_periodo.get("emissores", {}),
        dt_atual_override=dt_atual,
        dt_anterior_override=dt_periodo,
    )
    diff_periodo_emissoes = comparar_snapshots(
        df_rows_or_map_atual=vigentes_emissoes,
        tipo_dataset="emissoes",
        key_fields=keys_emissoes,
        map_anterior_override=snap_periodo.get("emissoes", {}),
        dt_atual_override=dt_atual,
        dt_anterior_override=dt_periodo,
    )

    resumo_periodo = {
        "upgrades_emissores": len(diff_periodo_emissores["upgrades"]),
        "upgrades_emissoes": len(diff_periodo_emissoes["upgrades"]),
        "total_upgrades": len(diff_periodo_emissores["upgrades"]) + len(diff_periodo_emissoes["upgrades"]),
        "downgrades_emissores": len(diff_periodo_emissores["downgrades"]),
        "downgrades_emissoes": len(diff_periodo_emissoes["downgrades"]),
        "total_downgrades": len(diff_periodo_emissores["downgrades"]) + len(diff_periodo_emissoes["downgrades"]),
        "novos_emissores": len(diff_periodo_emissores["novos"]),
        "novos_emissoes": len(diff_periodo_emissoes["novos"]),
        "total_novos": len(diff_periodo_emissores["novos"]) + len(diff_periodo_emissoes["novos"]),
        "outlooks_emissores": len(diff_periodo_emissores["outlooks"]),
        "outlooks_emissoes": len(diff_periodo_emissoes["outlooks"]),
        "total_outlooks": len(diff_periodo_emissores["outlooks"]) + len(diff_periodo_emissoes["outlooks"]),
        "retirados_emissores": len(diff_periodo_emissores["retirados"]),
        "retirados_emissoes": len(diff_periodo_emissoes["retirados"]),
        "total_retirados": len(diff_periodo_emissores["retirados"]) + len(diff_periodo_emissoes["retirados"]),
    }

    # 2. Comparativo da Última Captura Diária (24h)
    logger.info(f"Comparando movimentações da última captura ({dt_diario} → {dt_atual})...")
    diff_diario_emissores = comparar_snapshots(
        df_rows_or_map_atual=vigentes_emissores,
        tipo_dataset="emissores",
        key_fields=keys_emissores,
        map_anterior_override=snap_diario.get("emissores", {}),
        dt_atual_override=dt_atual,
        dt_anterior_override=dt_diario,
    )
    diff_diario_emissoes = comparar_snapshots(
        df_rows_or_map_atual=vigentes_emissoes,
        tipo_dataset="emissoes",
        key_fields=keys_emissoes,
        map_anterior_override=snap_diario.get("emissoes", {}),
        dt_atual_override=dt_atual,
        dt_anterior_override=dt_diario,
    )

    resumo_diario = {
        "upgrades_emissores": len(diff_diario_emissores["upgrades"]),
        "upgrades_emissoes": len(diff_diario_emissoes["upgrades"]),
        "total_upgrades": len(diff_diario_emissores["upgrades"]) + len(diff_diario_emissoes["upgrades"]),
        "downgrades_emissores": len(diff_diario_emissores["downgrades"]),
        "downgrades_emissoes": len(diff_diario_emissoes["downgrades"]),
        "total_downgrades": len(diff_diario_emissores["downgrades"]) + len(diff_diario_emissoes["downgrades"]),
        "novos_emissores": len(diff_diario_emissores["novos"]),
        "novos_emissoes": len(diff_diario_emissoes["novos"]),
        "total_novos": len(diff_diario_emissores["novos"]) + len(diff_diario_emissoes["novos"]),
        "outlooks_emissores": len(diff_diario_emissores["outlooks"]),
        "outlooks_emissoes": len(diff_diario_emissoes["outlooks"]),
        "total_outlooks": len(diff_diario_emissores["outlooks"]) + len(diff_diario_emissoes["outlooks"]),
        "retirados_emissores": len(diff_diario_emissores["retirados"]),
        "retirados_emissoes": len(diff_diario_emissoes["retirados"]),
        "total_retirados": len(diff_diario_emissores["retirados"]) + len(diff_diario_emissoes["retirados"]),
    }

    # 3. Lista de movimentações do período para exibição
    periodo_movs = []
    for cat, diff in [("Emissor", diff_periodo_emissores), ("Emissão", diff_periodo_emissoes)]:
        for item in diff.get("upgrades", []):
            periodo_movs.append({**item, "categoria": cat, "tipo": "UPGRADE", "dt_captura": dt_atual})
        for item in diff.get("downgrades", []):
            periodo_movs.append({**item, "categoria": cat, "tipo": "DOWNGRADE", "dt_captura": dt_atual})
        for item in diff.get("novos", []):
            periodo_movs.append({**item, "categoria": cat, "tipo": "NOVO", "dt_captura": dt_atual})
        for item in diff.get("outlooks", []):
            periodo_movs.append({**item, "categoria": cat, "tipo": "OUTLOOK", "dt_captura": dt_atual})
        for item in diff.get("retirados", []):
            periodo_movs.append({**item, "categoria": cat, "tipo": "RETIRADO", "dt_captura": dt_atual})

    periodo_movs.sort(key=lambda m: str(m.get("dt_acao") or ""), reverse=True)

    # 4. Salva histórico cumulativo contínuo
    salvar_historico_movimentacoes(data_dir=data_dir, novos_eventos=periodo_movs)

    # Carrega histórico completo acumulado de data/historico_movimentacoes.csv
    hist_completo = []
    hist_path = data_dir / "historico_movimentacoes.csv"
    if hist_path.exists():
        with open(hist_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                hist_completo.append({
                    "agencia": r.get("agencia"),
                    "emissor": r.get("no_emissor_padronizado"),
                    "instrumento": r.get("de_instrumento"),
                    "categoria": r.get("categoria"),
                    "tipo": r.get("tipo_movimento"),
                    "tipo_movimento": r.get("tipo_movimento"),
                    "rating_anterior": r.get("rating_anterior"),
                    "rating_atual": r.get("rating_atual"),
                    "variacao_notches": r.get("variacao_notches"),
                    "outlook_anterior": r.get("outlook_anterior"),
                    "outlook_atual": r.get("outlook_atual"),
                    "dt_acao": r.get("dt_acao_rating"),
                    "dt_captura": r.get("dt_captura"),
                    "link": r.get("link"),
                })

    relatorio = {
        "timestamp": datetime.now().isoformat(),
        "dt_atual": dt_atual,
        "dt_anterior": dt_diario,
        "resumo": resumo_periodo,
        "periodo_recente": {
            "dt_atual": dt_atual,
            "dt_anterior": dt_periodo,
            "resumo": resumo_periodo,
            "emissores": diff_periodo_emissores,
            "emissoes": diff_periodo_emissoes,
        },
        "diario": {
            "dt_atual": dt_atual,
            "dt_anterior": dt_diario,
            "resumo": resumo_diario,
            "emissores": diff_diario_emissores,
            "emissoes": diff_diario_emissoes,
        },
        "movimentacoes": periodo_movs,
        "historico_completo": hist_completo,
        "emissores": diff_periodo_emissores,
        "emissoes": diff_periodo_emissoes,
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

    # Salva Markdown atual
    md_content = gerar_markdown(relatorio)
    md_path = data_dir / "movimentacoes_ratings.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"Relatório Markdown salvo em {md_path}")

    # Salva arquivo histórico de relatório arquivado
    relatorios_dir = data_dir / "relatorios_movimentacoes"
    relatorios_dir.mkdir(parents=True, exist_ok=True)
    rel_hist_file = relatorios_dir / f"relatorio_movimentacoes_{dt_atual}.md"
    with open(rel_hist_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"Relatório histórico arquivado em {rel_hist_file}")

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
    res = rel["resumo"]
    print(f"\nResumo de Movimentações do Período ({formatar_data_br(rel['periodo_recente']['dt_anterior'])} → {formatar_data_br(rel['dt_atual'])}):")
    print(f"  🟢 Upgrades:    {res['total_upgrades']}")
    print(f"  🔴 Downgrades:  {res['total_downgrades']}")
    print(f"  🔵 Novos:       {res['total_novos']}")
    print(f"  🟡 Outlooks:    {res['total_outlooks']}")
    print(f"  ⚪ Retirados:   {res['total_retirados']}")
    print(f"  📚 Histórico Total: {len(rel['historico_completo'])} eventos registrados")
