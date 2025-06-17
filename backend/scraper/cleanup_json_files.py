#!/usr/bin/env python3
"""
Script para limpeza manual de arquivos JSON órfãos
"""

import sys
import json
import time
import argparse
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.monitoring.api_worker import APIWorker


def cleanup_json_files(
    json_dir: str = None,
    max_age_hours: int = 24,
    dry_run: bool = False,
    force: bool = False,
):
    """
    Limpa arquivos JSON órfãos

    Args:
        json_dir: Diretório dos arquivos JSON (padrão: reports/json)
        max_age_hours: Idade máxima em horas para considerar órfão
        dry_run: Apenas mostra o que seria removido sem remover
        force: Remove todos os arquivos independente da fila Redis
    """

    # Usar diretório padrão se não especificado
    if json_dir is None:
        script_dir = Path(__file__).parent
        json_dir = script_dir / "reports" / "json"
    else:
        json_dir = Path(json_dir)

    if not json_dir.exists():
        print(f"❌ Diretório não encontrado: {json_dir}")
        return 0

    print(f"🧹 Verificando arquivos JSON em: {json_dir}")
    print(f"⏰ Idade máxima: {max_age_hours} horas")
    print(f"🔍 Modo dry-run: {'Sim' if dry_run else 'Não'}")
    print(f"💪 Modo força: {'Sim' if force else 'Não'}")
    print("-" * 50)

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    json_files = list(json_dir.glob("*.json"))
    print(f"📄 Total de arquivos JSON encontrados: {len(json_files)}")

    if len(json_files) == 0:
        print("✅ Nenhum arquivo JSON para processar")
        return 0

    # Conectar ao Redis apenas se não for modo força
    worker = None
    if not force:
        try:
            print("🔗 Conectando ao Redis para verificar filas...")
            worker = APIWorker(
                redis_url="redis://localhost:6379/0",
                api_endpoint="http://localhost:8000",
                log_path="./logs",
            )
            worker.redis_client = worker._connect_redis()
            print("✅ Conectado ao Redis")
        except Exception as e:
            print(f"❌ Erro ao conectar Redis: {e}")
            print("⚠️ Continuando sem verificação de fila...")
            worker = None

    removed_count = 0
    skipped_count = 0

    for json_file in json_files:
        try:
            file_age = current_time - json_file.stat().st_mtime
            file_age_hours = file_age / 3600

            should_remove = False
            reason = ""

            if file_age > max_age_seconds:
                if force:
                    should_remove = True
                    reason = f"idade: {file_age_hours:.1f}h (modo força)"
                elif worker and not worker._is_file_in_queue(json_file.name):
                    should_remove = True
                    reason = f"idade: {file_age_hours:.1f}h (não está na fila)"
                elif not worker:
                    should_remove = True
                    reason = f"idade: {file_age_hours:.1f}h (Redis indisponível)"
                else:
                    reason = f"idade: {file_age_hours:.1f}h (ainda na fila)"
            else:
                reason = f"idade: {file_age_hours:.1f}h (muito novo)"

            if should_remove:
                if dry_run:
                    print(f"🗑️ SERIA REMOVIDO: {json_file.name} ({reason})")
                    removed_count += 1
                else:
                    json_file.unlink()
                    print(f"🗑️ REMOVIDO: {json_file.name} ({reason})")
                    removed_count += 1
            else:
                print(f"⏭️ MANTIDO: {json_file.name} ({reason})")
                skipped_count += 1

        except Exception as e:
            print(f"❌ Erro ao processar {json_file.name}: {e}")
            skipped_count += 1

    # Fechar conexão Redis
    if worker and worker.redis_client:
        worker.redis_client.close()

    print("-" * 50)
    print(f"📊 RESUMO:")
    print(f"   🗑️ Arquivos removidos: {removed_count}")
    print(f"   ⏭️ Arquivos mantidos: {skipped_count}")
    print(f"   📄 Total processado: {removed_count + skipped_count}")

    if dry_run and removed_count > 0:
        print(
            f"\n💡 Execute novamente sem --dry-run para remover {removed_count} arquivos"
        )

    return removed_count


def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description="Limpa arquivos JSON órfãos",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--json-dir", help="Diretório dos arquivos JSON (padrão: reports/json)"
    )

    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=24,
        help="Idade máxima em horas para considerar órfão",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas mostra o que seria removido sem remover",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove todos os arquivos independente da fila Redis",
    )

    args = parser.parse_args()

    print("🧹 LIMPEZA DE ARQUIVOS JSON ÓRFÃOS")
    print("=" * 40)

    if args.force:
        response = input(
            "⚠️ MODO FORÇA ativado! Isso removerá TODOS os arquivos antigos independente da fila. Confirma? (sim/não): "
        )
        if response.lower() not in ["sim", "s", "yes", "y"]:
            print("❌ Operação cancelada")
            return

    try:
        removed_count = cleanup_json_files(
            json_dir=args.json_dir,
            max_age_hours=args.max_age_hours,
            dry_run=args.dry_run,
            force=args.force,
        )

        if removed_count > 0:
            print(f"\n✅ Limpeza concluída com sucesso!")
        else:
            print(f"\n✅ Nenhum arquivo precisou ser removido")

    except KeyboardInterrupt:
        print(f"\n⏹️ Operação interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante limpeza: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
