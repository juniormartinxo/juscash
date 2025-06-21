#!/usr/bin/env python3
"""
Monitor de progresso para o Multi-Date Multi-Worker Scraper
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path
import argparse


def load_progress_data(json_file_path):
    """Carrega dados de progresso do arquivo JSON"""
    try:
        if not Path(json_file_path).exists():
            return None

        with open(json_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo de progresso: {e}")
        return None


def format_duration(start_time_str, end_time_str=None):
    """Formatar duração entre dois tempos"""
    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = (
            datetime.fromisoformat(end_time_str) if end_time_str else datetime.now()
        )
        duration = end_time - start_time

        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h{minutes:02d}m{seconds:02d}s"
        elif minutes > 0:
            return f"{minutes}m{seconds:02d}s"
        else:
            return f"{seconds}s"
    except:
        return "N/A"


def print_header():
    """Imprime cabeçalho do monitor"""
    print("=" * 80)
    print("🕷️  MONITOR DE PROGRESSO - MULTI-DATE SCRAPER")
    print("=" * 80)


def print_metadata(metadata):
    """Imprime metadados do progresso"""
    print("\n📊 RESUMO GERAL:")
    print("-" * 40)
    print(f"📅 Período: {metadata.get('start_date')} até {metadata.get('end_date')}")
    print(f"👥 Workers: {metadata.get('num_workers')}")
    print(f"🔄 Última atualização: {metadata.get('last_updated')}")
    print(f"📈 Total de datas: {metadata.get('total_dates')}")
    print(f"✅ Datas processadas: {metadata.get('processed_dates')}")
    print(f"📄 Total de publicações: {metadata.get('total_publications')}")

    if metadata.get("total_dates", 0) > 0:
        progress_percent = (
            metadata.get("processed_dates", 0) / metadata.get("total_dates", 1)
        ) * 100
        print(f"🎯 Progresso: {progress_percent:.1f}%")


def print_workers_status(workers):
    """Imprime status dos workers"""
    if not workers:
        print("\n👥 WORKERS: Nenhum worker ativo")
        return

    print("\n👥 STATUS DOS WORKERS:")
    print("-" * 40)

    for worker_id, worker_data in workers.items():
        status_emoji = {
            "idle": "😴",
            "working": "🔥",
            "completed": "✅",
            "error": "❌",
        }.get(worker_data.get("status", "unknown"), "❓")

        current_date = worker_data.get("current_date", "N/A")
        dates_processed = worker_data.get("dates_processed", 0)
        total_publications = worker_data.get("total_publications", 0)

        print(f"{status_emoji} {worker_id}: {worker_data.get('status', 'unknown')}")
        print(f"   📅 Data atual: {current_date}")
        print(f"   ✅ Datas processadas: {dates_processed}")
        print(f"   📄 Publicações: {total_publications}")


def print_recent_dates(dates, limit=10):
    """Imprime datas processadas recentemente"""
    if not dates:
        return

    # Filtrar datas processadas e ordenar por data de fim
    processed_dates = [
        (date_str, date_data)
        for date_str, date_data in dates.items()
        if date_data.get("processed") and date_data.get("end_time")
    ]

    # Ordenar por end_time (mais recentes primeiro)
    processed_dates.sort(key=lambda x: x[1].get("end_time", ""), reverse=True)

    print(f"\n📅 ÚLTIMAS {min(limit, len(processed_dates))} DATAS PROCESSADAS:")
    print("-" * 40)

    for date_str, date_data in processed_dates[:limit]:
        worker_id = date_data.get("worker_id", "N/A")
        publications = date_data.get("publications_found", 0)
        duration = format_duration(
            date_data.get("start_time", ""), date_data.get("end_time", "")
        )

        print(f"📅 {date_str} | 👷 {worker_id} | 📄 {publications} pub | ⏱️ {duration}")


def print_failed_dates(dates):
    """Imprime datas que falharam"""
    failed_dates = [
        (date_str, date_data)
        for date_str, date_data in dates.items()
        if date_data.get("error") and not date_data.get("processed")
    ]

    if failed_dates:
        print(f"\n❌ DATAS COM ERRO ({len(failed_dates)}):")
        print("-" * 40)

        for date_str, date_data in failed_dates[:5]:  # Mostrar apenas 5
            error = (
                date_data.get("error", "")[:60] + "..."
                if len(date_data.get("error", "")) > 60
                else date_data.get("error", "")
            )
            retry_count = date_data.get("retry_count", 0)
            print(f"📅 {date_str} | 🔄 Tentativas: {retry_count} | ❌ {error}")


def print_statistics(dates):
    """Imprime estatísticas detalhadas"""
    if not dates:
        return

    processed = sum(1 for d in dates.values() if d.get("processed"))
    failed = sum(1 for d in dates.values() if d.get("error") and not d.get("processed"))
    pending = len(dates) - processed - failed

    total_publications = sum(d.get("publications_found", 0) for d in dates.values())
    avg_publications = total_publications / max(processed, 1)

    print(f"\n📊 ESTATÍSTICAS DETALHADAS:")
    print("-" * 40)
    print(f"✅ Processadas: {processed}")
    print(f"❌ Com erro: {failed}")
    print(f"⏳ Pendentes: {pending}")
    print(f"📄 Total de publicações: {total_publications}")
    print(f"📊 Média por data: {avg_publications:.1f}")


def monitor_once(json_file_path):
    """Executa um ciclo de monitoramento"""
    data = load_progress_data(json_file_path)

    if not data:
        print(f"❌ Não foi possível carregar dados de {json_file_path}")
        return False

    print_header()
    print_metadata(data.get("metadata", {}))
    print_workers_status(data.get("workers", {}))
    print_recent_dates(data.get("dates", {}))
    print_failed_dates(data.get("dates", {}))
    print_statistics(data.get("dates", {}))

    return True


def monitor_continuous(json_file_path, interval=30):
    """Monitor contínuo com refresh automático"""
    try:
        while True:
            os.system("clear" if os.name == "posix" else "cls")  # Limpar tela

            if not monitor_once(json_file_path):
                print(f"\n⏳ Aguardando arquivo de progresso em {json_file_path}...")

            print(f"\n🔄 Próxima atualização em {interval}s... (Ctrl+C para sair)")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n👋 Monitor finalizado pelo usuário")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Monitor de progresso do Multi-Date Scraper"
    )
    parser.add_argument(
        "--file",
        "-f",
        default="src/scrap_workrs.json",
        help="Caminho para o arquivo de progresso JSON",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=30,
        help="Intervalo de atualização em segundos (padrão: 30)",
    )
    parser.add_argument(
        "--once",
        "-o",
        action="store_true",
        help="Executar apenas uma vez (sem loop contínuo)",
    )

    args = parser.parse_args()

    if args.once:
        monitor_once(args.file)
    else:
        monitor_continuous(args.file, args.interval)


if __name__ == "__main__":
    main()
