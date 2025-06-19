"""
Exemplo completo de teste e configuração do sistema DJE
Demonstra como usar o parser aprimorado com páginas divididas
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.logging.logger import setup_logger
from infrastructure.config.settings import get_settings

logger = setup_logger(__name__)


class DJESystemTester:
    """
    Classe para testar o sistema completo de extração DJE
    """

    def __init__(self):
        self.settings = get_settings()
        self.test_results = []

    async def run_complete_test(self):
        """
        Executa teste completo do sistema
        """
        logger.info("🧪 Iniciando teste completo do sistema DJE")
        
        # 1. Teste do parser com conteúdo simples
        await self._test_simple_content_parsing()
        
        # 2. Teste do parser com conteúdo dividido (simulado)
        await self._test_cross_page_content_parsing()
        
        # 3. Teste do scraper completo (opcional - requer internet)
        await self._test_full_scraper_integration()
        
        # 4. Gerar relatório de testes
        self._generate_test_report()

    async def _test_simple_content_parsing(self):
        """
        Testa parsing de conteúdo simples com RPV
        """
        logger.info("📋 Teste 1: Parsing de conteúdo simples")
        
        try:
            from infrastructure.web.enhanced_content_parser import EnhancedDJEContentParser
            
            parser = EnhancedDJEContentParser()
            
            # Conteúdo de teste simulando uma publicação real
            test_content = """
            Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença contra a Fazenda Pública
            - JOÃO DA SILVA SANTOS - Vistos. O requerente solicita RPV para pagamento pelo INSS
            do valor de R$ 5.450,30 referente a benefício previdenciário. ADV. MARIA OLIVEIRA 
            (OAB 123456/SP). Valor principal: R$ 5.450,30. Juros moratórios: R$ 150,20.
            Honorários advocatícios: R$ 545,03.
            
            Processo 7654321-12.2024.8.26.0002 - Outro processo diferente
            - PEDRO SOUZA - Vistos. Processo não relacionado ao INSS.
            """
            
            publications = await parser.parse_multiple_publications_enhanced(
                test_content, 
                "test_url", 
                1
            )
            
            if publications:
                logger.info(f"✅ Teste 1 PASSOU: {len(publications)} publicações extraídas")
                for pub in publications:
                    logger.info(f"   📋 {pub.process_number} - Autores: {pub.authors}")
                self.test_results.append(("Simple Content Parsing", "PASSOU", len(publications)))
            else:
                logger.error("❌ Teste 1 FALHOU: Nenhuma publicação extraída")
                self.test_results.append(("Simple Content Parsing", "FALHOU", 0))
                
        except Exception as e:
            logger.error(f"❌ Teste 1 ERRO: {e}")
            self.test_results.append(("Simple Content Parsing", "ERRO", str(e)))

    async def _test_cross_page_content_parsing(self):
        """
        Testa parsing de conteúdo dividido entre páginas (simulado)
        """
        logger.info("📋 Teste 2: Parsing de conteúdo dividido entre páginas")
        
        try:
            from infrastructure.web.enhanced_content_parser import EnhancedDJEContentParser
            from infrastructure.web.page_manager import PublicationContentMerger
            
            parser = EnhancedDJEContentParser()
            merger = PublicationContentMerger()
            
            # Simular conteúdo da página anterior (fim de uma publicação)
            previous_page_content = """
            Processo 1234567-89.2024.8.26.0001 - Cumprimento de Sentença contra a Fazenda Pública
            - JOÃO DA SILVA SANTOS - Vistos. O requerente solicita
            """
            
            # Simular conteúdo da página atual (continuação + RPV)
            current_page_content = """
            RPV para pagamento pelo INSS do valor de R$ 5.450,30 referente a benefício
            previdenciário. ADV. MARIA OLIVEIRA (OAB 123456/SP). Valor principal: R$ 5.450,30.
            
            Processo 7654321-12.2024.8.26.0002 - Outro processo
            - PEDRO SOUZA - Vistos. Processo diferente.
            """
            
            # Testar merge de conteúdo
            merged_content = merger.merge_cross_page_publication(
                previous_page_content,
                current_page_content,
                0  # Posição do RPV na página atual
            )
            
            # Validar merge
            is_valid = merger.validate_merged_content(merged_content, ['rpv', 'pagamento pelo inss'])
            
            if is_valid:
                logger.info("✅ Teste 2a PASSOU: Merge de páginas validado")
                
                # Testar parsing do conteúdo merged
                publications = await parser.parse_multiple_publications_enhanced(
                    merged_content,
                    "test_url_merged",
                    2
                )
                
                if publications:
                    logger.info(f"✅ Teste 2b PASSOU: {len(publications)} publicações extraídas do conteúdo merged")
                    self.test_results.append(("Cross-Page Content Parsing", "PASSOU", len(publications)))
                else:
                    logger.error("❌ Teste 2b FALHOU: Nenhuma publicação extraída do conteúdo merged")
                    self.test_results.append(("Cross-Page Content Parsing", "FALHOU", 0))
            else:
                logger.error("❌ Teste 2a FALHOU: Merge de páginas inválido")
                self.test_results.append(("Cross-Page Content Parsing", "FALHOU", "Merge inválido"))
                
        except Exception as e:
            logger.error(f"❌ Teste 2 ERRO: {e}")
            self.test_results.append(("Cross-Page Content Parsing", "ERRO", str(e)))

    async def _test_full_scraper_integration(self):
        """
        Teste completo do scraper (opcional - requer internet)
        """
        logger.info("📋 Teste 3: Integração completa do scraper (OPCIONAL)")
        
        try:
            # Só executar se configurado para testes completos
            if not self.settings.get("ENABLE_FULL_INTEGRATION_TESTS", False):
                logger.info("ℹ️ Testes de integração completa desabilitados")
                self.test_results.append(("Full Scraper Integration", "PULADO", "Desabilitado"))
                return
            
            from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
            
            scraper = DJEScraperAdapter()
            
            try:
                await scraper.initialize()
                
                # Definir data específica para teste
                scraper.set_target_date("17/03/2025")
                
                # Testar scraping limitado (apenas 1 página)
                search_terms = ["RPV", "pagamento pelo INSS"]
                publications_found = 0
                
                async for publication in scraper.scrape_publications(search_terms, max_pages=1):
                    publications_found += 1
                    logger.info(f"📋 Publicação encontrada: {publication.process_number}")
                    
                    # Limitar para não sobrecarregar o teste
                    if publications_found >= 3:
                        break
                
                if publications_found > 0:
                    logger.info(f"✅ Teste 3 PASSOU: {publications_found} publicações encontradas")
                    self.test_results.append(("Full Scraper Integration", "PASSOU", publications_found))
                else:
                    logger.warning("⚠️ Teste 3 PARCIAL: Nenhuma publicação encontrada (pode ser normal)")
                    self.test_results.append(("Full Scraper Integration", "PARCIAL", 0))
                    
            finally:
                await scraper.cleanup()
                
        except Exception as e:
            logger.error(f"❌ Teste 3 ERRO: {e}")
            self.test_results.append(("Full Scraper Integration", "ERRO", str(e)))

    def _generate_test_report(self):
        """
        Gera relatório final dos testes
        """
        logger.info("📊 Gerando relatório de testes")
        
        print("\n" + "="*80)
        print("📋 RELATÓRIO DE TESTES DO SISTEMA DJE")
        print("="*80)
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Total de Testes: {len(self.test_results)}")
        print("-"*80)
        
        passed = 0
        failed = 0
        errors = 0
        skipped = 0
        
        for test_name, status, result in self.test_results:
            status_icon = {
                "PASSOU": "✅",
                "FALHOU": "❌", 
                "ERRO": "🔥",
                "PARCIAL": "⚠️",
                "PULADO": "⏭️"
            }.get(status, "❓")
            
            print(f"{status_icon} {test_name:<40} {status:<10} {result}")
            
            if status == "PASSOU":
                passed += 1
            elif status == "FALHOU":
                failed += 1
            elif status == "ERRO":
                errors += 1
            elif status == "PULADO":
                skipped += 1
        
        print("-"*80)
        print(f"✅ Passou: {passed}")
        print(f"❌ Falhou: {failed}")
        print(f"🔥 Erro: {errors}")
        print(f"⏭️ Pulado: {skipped}")
        print("="*80)
        
        # Salvar relatório em arquivo
        self._save_test_report_to_file()

    def _save_test_report_to_file(self):
        """
        Salva relatório em arquivo
        """
        try:
            report_dir = Path("logs/test_reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"dje_test_report_{timestamp}.txt"
            
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("RELATÓRIO DE TESTES DO SISTEMA DJE\n")
                f.write("="*50 + "\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Total de Testes: {len(self.test_results)}\n\n")
                
                for test_name, status, result in self.test_results:
                    f.write(f"{test_name}: {status} - {result}\n")
            
            logger.info(f"📄 Relatório salvo em: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar relatório: {e}")


class DJEConfigurationHelper:
    """
    Helper para configuração do sistema DJE
    """

    @staticmethod
    def check_dependencies():
        """
        Verifica dependências necessárias
        """
        logger.info("🔍 Verificando dependências...")
        
        dependencies = {
            "playwright": "Playwright (para automação web)",
            "PyPDF2": "PyPDF2 (para extração de PDF) - OPCIONAL", 
            "pdfplumber": "pdfplumber (para extração de PDF) - OPCIONAL",
            "loguru": "Loguru (para logging)",
            "httpx": "HTTPX (para requisições HTTP)"
        }
        
        missing = []
        
        for dep, description in dependencies.items():
            try:
                __import__(dep)
                logger.info(f"✅ {description}")
            except ImportError:
                if dep in ["PyPDF2", "pdfplumber"]:
                    logger.warning(f"⚠️ {description} - OPCIONAL")
                else:
                    logger.error(f"❌ {description} - OBRIGATÓRIO")
                    missing.append(dep)
        
        if missing:
            logger.error(f"❌ Dependências obrigatórias ausentes: {missing}")
            logger.error("💡 Execute: pip install " + " ".join(missing))
            return False
        
        logger.info("✅ Todas as dependências obrigatórias estão instaladas")
        return True

    @staticmethod
    def setup_directories():
        """
        Cria diretórios necessários
        """
        directories = [
            "logs",
            "logs/debug_images", 
            "logs/test_reports",
            "data/json_reports",
            "data/temp_pdfs"
        ]
        
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Diretório criado/verificado: {dir_path}")

    @staticmethod
    def validate_configuration():
        """
        Valida configuração do sistema
        """
        logger.info("⚙️ Validando configuração...")
        
        settings = get_settings()
        
        # Verificar configurações críticas
        required_settings = [
            "browser.timeout",
            "browser.user_agent"
        ]
        
        missing_settings = []
        
        for setting in required_settings:
            try:
                value = settings
                for part in setting.split('.'):
                    value = getattr(value, part)
                if value:
                    logger.info(f"✅ {setting}: configurado")
                else:
                    missing_settings.append(setting)
            except AttributeError:
                missing_settings.append(setting)
        
        if missing_settings:
            logger.error(f"❌ Configurações ausentes: {missing_settings}")
            return False
        
        logger.info("✅ Configuração validada")
        return True


async def main():
    """
    Função principal para executar testes
    """
    print("🌟 SISTEMA DE EXTRAÇÃO DJE-SP - TESTE COMPLETO")
    print("="*60)
    
    # 1. Verificar dependências
    config_helper = DJEConfigurationHelper()
    
    if not config_helper.check_dependencies():
        print("❌ Falha na verificação de dependências")
        return 1
    
    # 2. Configurar diretórios
    config_helper.setup_directories()
    
    # 3. Validar configuração
    if not config_helper.validate_configuration():
        print("❌ Falha na validação de configuração")
        return 1
    
    # 4. Executar testes
    tester = DJESystemTester()
    await tester.run_complete_test()
    
    print("\n🎉 Testes concluídos! Verifique o relatório acima.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
