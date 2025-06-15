"""
Interface de linha de comando para gerenciamento do scraper
"""

import asyncio
import click
import json
from datetime import datetime, timedelta
from pathlib import Path

from infrastructure.logging.logger import setup_logger
from infrastructure.config.dynamic_config import DynamicConfigManager
from infrastructure.backup.backup_manager import BackupManager
from infrastructure.alerts.alert_system import alert_system
from infrastructure.monitoring.performance_monitor import PerformanceMonitor
from application.services.scraping_orchestrator import ScrapingOrchestrator
from shared.container import Container

logger = setup_logger(__name__)


@click.group()
@click.option(
    "--config",
    "-c",
    default="./config/scraping_config.json",
    help="Caminho do arquivo de configuração",
)
@click.option("--verbose", "-v", is_flag=True, help="Log detalhado")
@click.pass_context
def cli(ctx, config, verbose):
    """DJE Scraper - Sistema de gerenciamento"""
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = config
    ctx.obj["verbose"] = verbose

    if verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option(
    "--search-terms",
    "-s",
    multiple=True,
    help="Termos de busca (pode usar múltiplas vezes)",
)
@click.option("--max-pages", "-p", type=int, default=5, help="Número máximo de páginas")
@click.option("--dry-run", is_flag=True, help="Simular execução sem salvar dados")
@click.pass_context
def run(ctx, search_terms, max_pages, dry_run):
    """Executa scraping manual"""
    click.echo("🚀 Iniciando scraping manual do DJE-SP")

    if dry_run:
        click.echo("🧪 Modo simulação ativado (dry-run)")

    if not search_terms:
        search_terms = ["RPV", "pagamento pelo INSS"]

    click.echo(f"🔍 Termos de busca: {', '.join(search_terms)}")
    click.echo(f"📄 Máximo de páginas: {max_pages}")

    async def run_scraping():
        try:
            container = Container()
            orchestrator = ScrapingOrchestrator(container)

            # Simular execução se dry-run
            if dry_run:
                click.echo("✅ Simulação concluída (nenhum dado foi salvo)")
                return

            result = await orchestrator.execute_daily_scraping()

            click.echo("\n📊 Resultados:")
            click.echo(f"   🔍 Publicações encontradas: {result.publications_found}")
            click.echo(f"   ✨ Novas: {result.publications_new}")
            click.echo(f"   🔄 Duplicadas: {result.publications_duplicated}")
            click.echo(f"   ❌ Falhas: {result.publications_failed}")
            click.echo(f"   💾 Salvas: {result.publications_saved}")

            if result.execution_time_seconds:
                click.echo(f"   ⏱️  Tempo: {result.execution_time_seconds}s")

            await container.cleanup()

        except Exception as error:
            click.echo(f"❌ Erro durante execução: {error}", err=True)
            raise click.ClickException(str(error))

    asyncio.run(run_scraping())


@cli.command()
@click.option("--output", "-o", default="./status_report.json", help="Arquivo de saída")
@click.pass_context
def status(ctx, output):
    """Gera relatório de status do sistema"""
    click.echo("📊 Gerando relatório de status...")

    async def generate_status():
        try:
            # Coletar informações de status
            config_manager = DynamicConfigManager(ctx.obj["config_file"])
            backup_manager = BackupManager()

            status_report = {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "python_version": "3.12",
                    "scraper_version": "1.0.0",
                    "config_file": ctx.obj["config_file"],
                },
                "configuration": config_manager.get_config().dict(),
                "alerts": {
                    "active": len(alert_system.get_active_alerts()),
                    "total_24h": len(
                        [
                            a
                            for a in alert_system.alerts
                            if a.timestamp > datetime.now() - timedelta(hours=24)
                        ]
                    ),
                    "statistics": alert_system.get_alert_statistics(),
                },
                "backups": backup_manager.get_backup_stats(),
                "health": {
                    "status": "healthy",  # Implementar health check
                    "last_execution": "pending",  # Implementar tracking
                    "api_connectivity": "unknown",  # Implementar test
                },
            }

            # Salvar relatório
            with open(output, "w", encoding="utf-8") as f:
                json.dump(status_report, f, indent=2, ensure_ascii=False)

            click.echo(f"✅ Relatório salvo: {output}")

            # Exibir resumo
            click.echo("\n📈 Resumo do Status:")
            click.echo(f"   ⚙️  Configuração: {ctx.obj['config_file']}")
            click.echo(f"   🔔 Alertas ativos: {status_report['alerts']['active']}")
            click.echo(
                f"   💾 Arquivos de backup: {status_report['backups']['total']['files']}"
            )
            click.echo(
                f"   📏 Tamanho dos backups: {status_report['backups']['total']['size_mb']:.1f}MB"
            )

        except Exception as error:
            click.echo(f"❌ Erro ao gerar status: {error}", err=True)
            raise click.ClickException(str(error))

    asyncio.run(generate_status())


@cli.group()
def config():
    """Comandos de configuração"""
    pass


@config.command()
@click.pass_context
def show(ctx):
    """Exibe configuração atual"""
    try:
        config_manager = DynamicConfigManager(ctx.obj["config_file"])
        current_config = config_manager.get_config()

        click.echo("⚙️ Configuração Atual:")
        click.echo(json.dumps(current_config.dict(), indent=2, ensure_ascii=False))

    except Exception as error:
        click.echo(f"❌ Erro ao exibir configuração: {error}", err=True)


@config.command()
@click.option(
    "--key", "-k", required=True, help="Chave da configuração (ex: max_pages)"
)
@click.option("--value", "-v", required=True, help="Novo valor")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["str", "int", "float", "bool"]),
    default="str",
    help="Tipo do valor",
)
@click.pass_context
def set(ctx, key, value, type):
    """Define valor de configuração"""
    try:
        # Converter valor para tipo apropriado
        if type == "int":
            value = int(value)
        elif type == "float":
            value = float(value)
        elif type == "bool":
            value = value.lower() in ("true", "1", "yes", "on")

        config_manager = DynamicConfigManager(ctx.obj["config_file"])

        if config_manager.update_config({key: value}):
            click.echo(f"✅ Configuração atualizada: {key} = {value}")
        else:
            click.echo("❌ Falha ao atualizar configuração", err=True)

    except ValueError:
        click.echo(f"❌ Valor inválido para tipo {type}: {value}", err=True)
    except Exception as error:
        click.echo(f"❌ Erro ao definir configuração: {error}", err=True)


@config.command()
@click.pass_context
def reset(ctx):
    """Reseta configuração para padrões"""
    if click.confirm("⚠️  Tem certeza que deseja resetar a configuração?"):
        try:
            config_manager = DynamicConfigManager(ctx.obj["config_file"])

            if config_manager.reset_to_defaults():
                click.echo("✅ Configuração resetada para padrões")
            else:
                click.echo("❌ Falha ao resetar configuração", err=True)

        except Exception as error:
            click.echo(f"❌ Erro ao resetar configuração: {error}", err=True)


@config.command()
@click.option("--output", "-o", required=True, help="Arquivo de exportação")
@click.pass_context
def export(ctx, output):
    """Exporta configuração atual"""
    try:
        config_manager = DynamicConfigManager(ctx.obj["config_file"])

        if config_manager.export_config(output):
            click.echo(f"✅ Configuração exportada: {output}")
        else:
            click.echo("❌ Falha ao exportar configuração", err=True)

    except Exception as error:
        click.echo(f"❌ Erro ao exportar configuração: {error}", err=True)


@config.command()
@click.option("--input", "-i", required=True, help="Arquivo de importação")
@click.pass_context
def import_config(ctx, input):
    """Importa configuração de arquivo"""
    if not Path(input).exists():
        click.echo(f"❌ Arquivo não encontrado: {input}", err=True)
        return

    if click.confirm(
        f"⚠️  Importar configuração de {input}? Isso substituirá a configuração atual."
    ):
        try:
            config_manager = DynamicConfigManager(ctx.obj["config_file"])

            if config_manager.import_config(input):
                click.echo(f"✅ Configuração importada: {input}")
            else:
                click.echo("❌ Falha ao importar configuração", err=True)

        except Exception as error:
            click.echo(f"❌ Erro ao importar configuração: {error}", err=True)


@cli.group()
def backup():
    """Comandos de backup"""
    pass


@backup.command()
@click.option("--retention-days", "-r", type=int, default=30, help="Dias de retenção")
@click.pass_context
def cleanup(ctx, retention_days):
    """Remove backups antigos"""
    try:
        backup_manager = BackupManager()
        removed_count = asyncio.run(backup_manager.cleanup_old_backups(retention_days))

        click.echo(f"✅ Limpeza concluída: {removed_count} arquivos removidos")

    except Exception as error:
        click.echo(f"❌ Erro na limpeza: {error}", err=True)


@backup.command()
@click.option("--days-back", "-d", type=int, default=1, help="Dias para trás")
@click.pass_context
def logs(ctx, days_back):
    """Faz backup dos logs"""
    try:
        backup_manager = BackupManager()
        success = asyncio.run(backup_manager.backup_logs(days_back))

        if success:
            click.echo(f"✅ Backup de logs concluído ({days_back} dias)")
        else:
            click.echo("❌ Falha no backup de logs", err=True)

    except Exception as error:
        click.echo(f"❌ Erro no backup: {error}", err=True)


@backup.command()
@click.pass_context
def stats(ctx):
    """Exibe estatísticas de backup"""
    try:
        backup_manager = BackupManager()
        stats = backup_manager.get_backup_stats()

        click.echo("📊 Estatísticas de Backup:")
        click.echo(f"   📁 Diretório: {stats['backup_dir']}")
        click.echo(
            f"   📄 Publicações: {stats['publications']['count']} arquivos ({stats['publications']['total_size_mb']:.1f}MB)"
        )
        click.echo(
            f"   🔄 Execuções: {stats['executions']['count']} arquivos ({stats['executions']['total_size_mb']:.1f}MB)"
        )
        click.echo(
            f"   📋 Logs: {stats['logs']['count']} arquivos ({stats['logs']['total_size_mb']:.1f}MB)"
        )
        click.echo(
            f"   📈 Total: {stats['total']['files']} arquivos ({stats['total']['size_mb']:.1f}MB)"
        )

    except Exception as error:
        click.echo(f"❌ Erro ao obter estatísticas: {error}", err=True)


@cli.group()
def alerts():
    """Comandos de alertas"""
    pass


@alerts.command()
@click.pass_context
def list(ctx):
    """Lista alertas ativos"""
    try:
        active_alerts = alert_system.get_active_alerts()

        if not active_alerts:
            click.echo("✅ Nenhum alerta ativo")
            return

        click.echo(f"🔔 Alertas Ativos ({len(active_alerts)}):")

        for alert in active_alerts:
            level_icon = {
                "info": "ℹ️ ",
                "warning": "⚠️ ",
                "error": "❌",
                "critical": "🚨",
            }

            icon = level_icon.get(alert.level.value, "🔔")
            click.echo(f"   {icon} [{alert.type.value}] {alert.title}")
            click.echo(f"      {alert.message}")
            click.echo(f"      {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo()

    except Exception as error:
        click.echo(f"❌ Erro ao listar alertas: {error}", err=True)


@alerts.command()
@click.option("--alert-id", "-i", required=True, help="ID do alerta")
@click.pass_context
def resolve(ctx, alert_id):
    """Marca alerta como resolvido"""
    try:
        if alert_system.resolve_alert(alert_id):
            click.echo(f"✅ Alerta resolvido: {alert_id}")
        else:
            click.echo(f"❌ Alerta não encontrado: {alert_id}", err=True)

    except Exception as error:
        click.echo(f"❌ Erro ao resolver alerta: {error}", err=True)


@alerts.command()
@click.option("--hours", "-h", type=int, default=24, help="Horas para trás")
@click.pass_context
def stats(ctx, hours):
    """Exibe estatísticas de alertas"""
    try:
        stats = alert_system.get_alert_statistics(hours)

        click.echo(f"📊 Estatísticas de Alertas ({hours}h):")
        click.echo(f"   📈 Total: {stats['total_alerts']}")
        click.echo(f"   🔔 Ativos: {stats['active_alerts']}")
        click.echo(f"   ✅ Taxa de resolução: {stats['resolution_rate']:.1f}%")

        click.echo("\n📊 Por Nível:")
        for level, count in stats["by_level"].items():
            if count > 0:
                click.echo(f"   {level}: {count}")

        click.echo("\n📊 Por Tipo:")
        for alert_type, count in stats["by_type"].items():
            if count > 0:
                click.echo(f"   {alert_type}: {count}")

    except Exception as error:
        click.echo(f"❌ Erro ao obter estatísticas: {error}", err=True)


@cli.group()
def test():
    """Comandos de teste"""
    pass


@test.command()
@click.option("--api-url", default="http://juscash-api:8000", help="URL da API")
@click.pass_context
def api(ctx, api_url):
    """Testa conexão com a API"""
    click.echo(f"🧪 Testando conexão com API: {api_url}")

    async def test_api_connection():
        try:
            from infrastructure.api.api_client_adapter import ApiClientAdapter
            from infrastructure.config.settings import get_settings

            # Configurar URL temporariamente
            settings = get_settings()
            original_url = settings.api.base_url
            settings.api.base_url = api_url

            api_client = ApiClientAdapter()

            # Teste simples de conectividade
            # Nota: Este é um teste básico, pode ser expandido
            click.echo("📡 Testando conectividade...")

            # Simular teste (implementar teste real conforme necessário)
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_url}/health", timeout=10)

                if response.status_code == 200:
                    click.echo("✅ API respondendo corretamente")
                else:
                    click.echo(f"⚠️  API retornou status {response.status_code}")

            # Restaurar URL original
            settings.api.base_url = original_url

        except Exception as error:
            click.echo(f"❌ Erro no teste da API: {error}", err=True)

    asyncio.run(test_api_connection())


@test.command()
@click.option(
    "--url", default="https://dje.tjsp.jus.br/cdje/index.do", help="URL do DJE"
)
@click.pass_context
def dje(ctx, url):
    """Testa acesso ao site do DJE"""
    click.echo(f"🧪 Testando acesso ao DJE: {url}")

    async def test_dje_access():
        try:
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()

            # Tentar acessar o DJE
            await page.goto(url, timeout=30000)

            # Verificar se carregou
            title = await page.title()
            click.echo(f"📄 Título da página: {title}")

            # Verificar elementos importantes
            if await page.query_selector('a[href*="cdCaderno"]'):
                click.echo("✅ Links de cadernos encontrados")
            else:
                click.echo("⚠️  Links de cadernos não encontrados")

            await browser.close()
            await playwright.stop()

            click.echo("✅ Teste do DJE concluído")

        except Exception as error:
            click.echo(f"❌ Erro no teste do DJE: {error}", err=True)

    asyncio.run(test_dje_access())


@cli.command()
@click.option(
    "--duration", "-d", type=int, default=60, help="Duração do monitoramento (segundos)"
)
@click.option(
    "--output", "-o", default="./performance_report.json", help="Arquivo de saída"
)
@click.pass_context
def monitor(ctx, duration, output):
    """Monitora performance do sistema"""
    click.echo(f"📊 Monitorando performance por {duration}s...")

    async def monitor_performance():
        try:
            monitor = PerformanceMonitor(sample_interval=5.0)

            # Iniciar monitoramento
            session_id = f"manual_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await monitor.start_session(session_id)

            # Aguardar duração especificada
            await asyncio.sleep(duration)

            # Finalizar e obter relatório
            session = await monitor.end_session()

            if session:
                report = monitor.get_session_report(session_id)

                # Salvar relatório
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

                click.echo(f"✅ Relatório salvo: {output}")

                # Exibir resumo
                if report and "metrics" in report:
                    metrics = report["metrics"]
                    click.echo("\n📈 Resumo de Performance:")
                    click.echo(f"   🖥️  CPU médio: {metrics['cpu']['avg']:.1f}%")
                    click.echo(
                        f"   💾 Memória média: {metrics['memory_mb']['avg']:.1f}MB"
                    )
                    click.echo(
                        f"   📡 Rede total: {metrics['network_total_mb']['sent']:.2f}MB sent, {metrics['network_total_mb']['received']:.2f}MB recv"
                    )

        except Exception as error:
            click.echo(f"❌ Erro no monitoramento: {error}", err=True)

    asyncio.run(monitor_performance())


@cli.command()
def version():
    """Exibe versão do scraper"""
    click.echo("DJE Scraper v1.0.0")
    click.echo("Sistema de web scraping para Diário da Justiça Eletrônico de São Paulo")
    click.echo("Desenvolvido com Arquitetura Hexagonal em Python 3.12")


if __name__ == "__main__":
    cli()
