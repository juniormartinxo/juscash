#!/usr/bin/env python3
"""
🎯 EXEMPLOS PRÁTICOS E SCRIPTS PRONTOS - SISTEMA DJE-SP

Este arquivo contém scripts prontos para uso em diferentes cenários.
Copie e adapte conforme sua necessidade.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# ==================================================================================
# 1. SCRIPT BÁSICO - EXTRAÇÃO DE UMA DATA ESPECÍFICA
# ==================================================================================

async def extract_single_date(target_date: str = None):
    """
    Extrai publicações de uma data específica
    
    Args:
        target_date: Data no formato DD/MM/YYYY (default: hoje)
    """
    if not target_date:
        target_date = datetime.now().strftime("%d/%m/%Y")
    
    print(f"🎯 Extraindo publicações para {target_date}")
    
    try:
        # Importar após adicionar src ao path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
        
        scraper = DJEScraperAdapter()
        await scraper.initialize()
        
        # Configurar data específica
        scraper.set_target_date(target_date)
        
        # Executar busca
        search_terms = ["RPV", "pagamento pelo INSS"]
        publications_count = 0
        
        async for publication in scraper.scrape_publications(search_terms, max_pages=3):
            publications_count += 1
            print(f"✅ {publications_count:02d}. {publication.process_number}")
            print(f"    👥 Autores: {', '.join(publication.authors[:2])}{'...' if len(publication.authors) > 2 else ''}")
            print(f"    💰 Valor: R$ {publication.gross_value.to_real() if publication.gross_value else 'N/A'}")
            print()
        
        print(f"📊 Total encontrado: {publications_count} publicações")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        if 'scraper' in locals():
            await scraper.cleanup()


# ==================================================================================
# 2. SCRIPT AVANÇADO - EXTRAÇÃO DE MÚLTIPLAS DATAS COM CONTROLE
# ==================================================================================

class AdvancedDateRangeScraper:
    """Scraper avançado para extrair múltiplas datas com controle fino"""
    
    def __init__(self):
        self.results = []
        self.failed_dates = []
        self.total_publications = 0
        
    async def extract_date_range(
        self, 
        start_date: str, 
        end_date: str,
        max_publications_per_date: int = 50,
        delay_between_dates: int = 5
    ):
        """
        Extrai publicações de um intervalo de datas
        
        Args:
            start_date: Data inicial (DD/MM/YYYY)
            end_date: Data final (DD/MM/YYYY)
            max_publications_per_date: Limite de publicações por data
            delay_between_dates: Delay em segundos entre datas
        """
        print(f"📅 Extraindo período: {start_date} até {end_date}")
        
        # Gerar lista de datas
        dates = self._generate_date_list(start_date, end_date)
        print(f"📋 Total de datas a processar: {len(dates)}")
        
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from infrastructure.web.dje_scraper_adapter import DJEScraperAdapter
        
        scraper = DJEScraperAdapter()
        await scraper.initialize()
        
        try:
            for i, date_str in enumerate(dates, 1):
                print(f"\n🔄 [{i:02d}/{len(dates)}] Processando {date_str}")
                
                try:
                    # Configurar data
                    scraper.set_target_date(date_str)
                    
                    # Extrair publicações desta data
                    date_publications = 0
                    search_terms = ["RPV", "pagamento pelo INSS"]
                    
                    async for publication in scraper.scrape_publications(search_terms, max_pages=5):
                        date_publications += 1
                        self.total_publications += 1
                        
                        print(f"    ✅ {date_publications:02d}. {publication.process_number}")
                        
                        if date_publications >= max_publications_per_date:
                            print(f"    ⚠️ Limite atingido ({max_publications_per_date})")
                            break
                    
                    self.results.append({
                        'date': date_str,
                        'publications_found': date_publications,
                        'status': 'success'
                    })
                    
                    print(f"    📊 {date_publications} publicações encontradas")
                    
                except Exception as e:
                    print(f"    ❌ Erro em {date_str}: {e}")
                    self.failed_dates.append(date_str)
                    self.results.append({
                        'date': date_str,
                        'publications_found': 0,
                        'status': 'failed',
                        'error': str(e)
                    })
                
                # Delay entre datas
                if i < len(dates):
                    print(f"    ⏳ Aguardando {delay_between_dates}s...")
                    await asyncio.sleep(delay_between_dates)
            
            # Relatório final
            self._print_final_report()
            
        finally:
            await scraper.cleanup()
    
    def _generate_date_list(self, start_date: str, end_date: str) -> List[str]:
        """Gera lista de datas entre start_date e end_date"""
        start = datetime.strptime(start_date, "%d/%m/%Y")
        end = datetime.strptime(end_date, "%d/%m/%Y")
        
        dates = []
        current = start
        
        while current <= end:
            dates.append(current.strftime("%d/%m/%Y"))
            current += timedelta(days=1)
        
        return dates
    
    def _print_final_report(self):
        """Imprime relatório final"""
        print(f"\n{'='*60}")
        print("📊 RELATÓRIO FINAL")
        print(f"{'='*60}")
        print(f"Total de publicações: {self.total_publications}")
        print(f"Datas processadas: {len([r for r in self.results if r['status'] == 'success'])}")
        print(f"Datas com falha: {len(self.failed_dates)}")
        
        if self.failed_dates:
            print(f"\n❌ Datas que falharam:")
            for date in self.failed_dates:
                print(f"   - {date}")
        
        # Top 5 datas com mais publicações
        successful_results = [r for r in self.results if r['status'] == 'success']
        if successful_results:
            top_dates = sorted(successful_results, key=lambda x: x['publications_found'], reverse=True)[:5]
            print(f"\n🏆 Top 5 datas com mais publicações:")
            for i, result in enumerate(top_dates, 1):
                print(f"   {i}. {result['date']}: {result['publications_found']} publicações")


# ==================================================================================
# 3. SCRIPT DE MONITORAMENTO E RELATÓRIOS
# ==================================================================================

class DJEAnalytics:
    """Classe para análise dos dados extraídos"""
    
    def __init__(self, json_dir: str = "data/json_reports"):
        self.json_dir = Path(json_dir)
        
    def generate_comprehensive_report(self):
        """Gera relatório abrangente dos dados"""
        print("📊 RELATÓRIO ABRANGENTE DJE-SP")
        print("="*60)
        
        # Carregar todos os JSONs
        publications = self._load_all_publications()
        
        if not publications:
            print("❌ Nenhuma publicação encontrada")
            return
        
        print(f"📋 Total de publicações: {len(publications)}")
        
        # Análises
        self._analyze_by_date(publications)
        self._analyze_by_authors(publications)
        self._analyze_monetary_values(publications)
        self._analyze_lawyers(publications)
        self._analyze_confidence_scores(publications)
        
    def _load_all_publications(self) -> List[Dict[str, Any]]:
        """Carrega todas as publicações dos arquivos JSON"""
        publications = []
        
        for json_file in self.json_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    publications.append(data)
            except Exception as e:
                print(f"⚠️ Erro ao ler {json_file}: {e}")
        
        return publications
    
    def _analyze_by_date(self, publications: List[Dict[str, Any]]):
        """Análise por data"""
        print(f"\n📅 ANÁLISE POR DATA")
        print("-" * 30)
        
        from collections import Counter
        
        date_counter = Counter()
        
        for pub in publications:
            date_str = pub.get("availability_date", "")[:10]  # YYYY-MM-DD
            if date_str:
                # Converter para DD/MM/YYYY
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d/%m/%Y")
                    date_counter[formatted_date] += 1
                except:
                    date_counter["Data inválida"] += 1
        
        # Top 10 datas
        print(f"🏆 Top 10 datas com mais publicações:")
        for i, (date, count) in enumerate(date_counter.most_common(10), 1):
            print(f"   {i:2d}. {date}: {count:3d} publicações")
    
    def _analyze_by_authors(self, publications: List[Dict[str, Any]]):
        """Análise por autores"""
        print(f"\n👥 ANÁLISE POR AUTORES")
        print("-" * 30)
        
        from collections import Counter
        
        author_counter = Counter()
        total_authors = 0
        
        for pub in publications:
            authors = pub.get("authors", [])
            total_authors += len(authors)
            
            for author in authors:
                # Normalizar nome (primeira e última palavra)
                words = author.split()
                if len(words) >= 2:
                    normalized = f"{words[0]} {words[-1]}"
                    author_counter[normalized] += 1
        
        print(f"📊 Total de autores únicos: {len(author_counter)}")
        print(f"📊 Média de autores por publicação: {total_authors/len(publications):.1f}")
        
        print(f"\n🏆 Top 10 autores mais frequentes:")
        for i, (author, count) in enumerate(author_counter.most_common(10), 1):
            print(f"   {i:2d}. {author}: {count} publicações")
    
    def _analyze_monetary_values(self, publications: List[Dict[str, Any]]):
        """Análise de valores monetários"""
        print(f"\n💰 ANÁLISE DE VALORES MONETÁRIOS")
        print("-" * 30)
        
        values_with_gross = [p for p in publications if p.get("gross_value")]
        
        if not values_with_gross:
            print("❌ Nenhuma publicação com valor bruto encontrada")
            return
        
        print(f"📊 Publicações com valor: {len(values_with_gross)}/{len(publications)} ({len(values_with_gross)/len(publications)*100:.1f}%)")
        
        # Converter centavos para reais
        gross_values = [p["gross_value"] / 100 for p in values_with_gross]
        
        # Estatísticas
        total_value = sum(gross_values)
        avg_value = total_value / len(gross_values)
        min_value = min(gross_values)
        max_value = max(gross_values)
        
        print(f"💰 Valor total: R$ {total_value:,.2f}")
        print(f"📊 Valor médio: R$ {avg_value:,.2f}")
        print(f"📉 Menor valor: R$ {min_value:,.2f}")
        print(f"📈 Maior valor: R$ {max_value:,.2f}")
        
        # Faixas de valor
        ranges = {
            "Até R$ 1.000": len([v for v in gross_values if v <= 1000]),
            "R$ 1.001 - R$ 5.000": len([v for v in gross_values if 1000 < v <= 5000]),
            "R$ 5.001 - R$ 10.000": len([v for v in gross_values if 5000 < v <= 10000]),
            "R$ 10.001 - R$ 50.000": len([v for v in gross_values if 10000 < v <= 50000]),
            "Acima de R$ 50.000": len([v for v in gross_values if v > 50000])
        }
        
        print(f"\n📊 Distribuição por faixas de valor:")
        for range_name, count in ranges.items():
            percentage = count / len(gross_values) * 100
            print(f"   {range_name}: {count} ({percentage:.1f}%)")
    
    def _analyze_lawyers(self, publications: List[Dict[str, Any]]):
        """Análise de advogados"""
        print(f"\n⚖️ ANÁLISE DE ADVOGADOS")
        print("-" * 30)
        
        from collections import Counter
        
        lawyer_counter = Counter()
        oab_counter = Counter()
        
        pubs_with_lawyers = [p for p in publications if p.get("lawyers")]
        
        print(f"📊 Publicações com advogados: {len(pubs_with_lawyers)}/{len(publications)} ({len(pubs_with_lawyers)/len(publications)*100:.1f}%)")
        
        if not pubs_with_lawyers:
            return
        
        for pub in pubs_with_lawyers:
            for lawyer in pub["lawyers"]:
                name = lawyer.get("name", "")
                oab = lawyer.get("oab", "")
                
                if name:
                    lawyer_counter[name] += 1
                if oab and oab != "Não informado":
                    oab_counter[oab] += 1
        
        print(f"📊 Total de advogados únicos: {len(lawyer_counter)}")
        print(f"📊 OABs únicos: {len(oab_counter)}")
        
        print(f"\n🏆 Top 5 advogados mais frequentes:")
        for i, (name, count) in enumerate(lawyer_counter.most_common(5), 1):
            print(f"   {i}. {name}: {count} publicações")
    
    def _analyze_confidence_scores(self, publications: List[Dict[str, Any]]):
        """Análise de scores de confiança"""
        print(f"\n🎯 ANÁLISE DE CONFIANÇA")
        print("-" * 30)
        
        scores = []
        for pub in publications:
            metadata = pub.get("extraction_metadata", {})
            score = metadata.get("confidence_score", 0)
            if score > 0:
                scores.append(score)
        
        if not scores:
            print("❌ Nenhum score de confiança encontrado")
            return
        
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        print(f"📊 Score médio: {avg_score:.3f}")
        print(f"📉 Score mínimo: {min_score:.3f}")
        print(f"📈 Score máximo: {max_score:.3f}")
        
        # Distribuição por faixas
        ranges = {
            "0.90 - 1.00 (Excelente)": len([s for s in scores if 0.90 <= s <= 1.00]),
            "0.80 - 0.89 (Bom)": len([s for s in scores if 0.80 <= s < 0.90]),
            "0.70 - 0.79 (Regular)": len([s for s in scores if 0.70 <= s < 0.80]),
            "Abaixo de 0.70 (Baixo)": len([s for s in scores if s < 0.70])
        }
        
        print(f"\n📊 Distribuição de confiança:")
        for range_name, count in ranges.items():
            percentage = count / len(scores) * 100
            print(f"   {range_name}: {count} ({percentage:.1f}%)")


# ==================================================================================
# 4. SCRIPT DE EXPORTAÇÃO E INTEGRAÇÃO
# ==================================================================================

class DJEExporter:
    """Classe para exportar dados em diferentes formatos"""
    
    def __init__(self, json_dir: str = "data/json_reports"):
        self.json_dir = Path(json_dir)
        
    def export_to_csv(self, output_file: str = None):
        """Exporta dados para CSV"""
        try:
            import pandas as pd
        except ImportError:
            print("❌ pandas não instalado. Execute: pip install pandas")
            return
        
        if not output_file:
            output_file = f"publicacoes_dje_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        print(f"📊 Exportando para CSV: {output_file}")
        
        # Carregar publicações
        publications = []
        for json_file in self.json_dir.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Converter valores para reais
                if data.get('gross_value'):
                    data['gross_value_reais'] = data['gross_value'] / 100
                if data.get('net_value'):
                    data['net_value_reais'] = data['net_value'] / 100
                if data.get('interest_value'):
                    data['interest_value_reais'] = data['interest_value'] / 100
                if data.get('attorney_fees'):
                    data['attorney_fees_reais'] = data['attorney_fees'] / 100
                
                # Extrair primeiro advogado
                lawyers = data.get('lawyers', [])
                if lawyers:
                    data['primeiro_advogado'] = lawyers[0].get('name', '')
                    data['primeiro_oab'] = lawyers[0].get('oab', '')
                
                # Extrair primeiro autor
                authors = data.get('authors', [])
                if authors:
                    data['primeiro_autor'] = authors[0]
                
                # Extrair confiança
                metadata = data.get('extraction_metadata', {})
                data['confidence_score'] = metadata.get('confidence_score', 0)
                
                publications.append(data)
        
        if not publications:
            print("❌ Nenhuma publicação encontrada")
            return
        
        # Criar DataFrame
        df = pd.DataFrame(publications)
        
        # Selecionar colunas importantes
        columns = [
            'process_number', 'availability_date', 'primeiro_autor', 
            'primeiro_advogado', 'primeiro_oab', 'gross_value_reais',
            'net_value_reais', 'confidence_score'
        ]
        
        # Manter apenas colunas que existem
        existing_columns = [col for col in columns if col in df.columns]
        df_export = df[existing_columns]
        
        # Exportar
        df_export.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ Exportado {len(df_export)} publicações para {output_file}")
        
    async def sync_with_api(self, api_url: str, api_key: str):
        """Sincroniza publicações com API externa"""
        try:
            import httpx
        except ImportError:
            print("❌ httpx não instalado. Execute: pip install httpx")
            return
        
        print(f"🔄 Sincronizando com API: {api_url}")
        
        sent_count = 0
        error_count = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for json_file in self.json_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    publication_data = json.load(f)
                
                try:
                    response = await client.post(
                        f"{api_url}/api/publications",
                        json=publication_data,
                        headers={
                            "X-API-Key": api_key,
                            "Content-Type": "application/json"
                        }
                    )
                    
                    if response.status_code in [200, 201]:
                        sent_count += 1
                        print(f"✅ {sent_count:03d}. {publication_data['process_number']}")
                        
                        # Mover para pasta "sent"
                        sent_dir = self.json_dir / "sent"
                        sent_dir.mkdir(exist_ok=True)
                        json_file.rename(sent_dir / json_file.name)
                        
                    else:
                        error_count += 1
                        print(f"❌ Erro {response.status_code}: {publication_data['process_number']}")
                        
                except Exception as e:
                    error_count += 1
                    print(f"❌ Exceção: {publication_data['process_number']} - {e}")
                
                # Pequeno delay entre requisições
                await asyncio.sleep(0.5)
        
        print(f"\n📊 Sincronização concluída:")
        print(f"   ✅ Enviados: {sent_count}")
        print(f"   ❌ Erros: {error_count}")


# ==================================================================================
# 5. FUNÇÕES UTILITÁRIAS
# ==================================================================================

def setup_logging():
    """Configura logging básico"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('dje_scripts.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Verifica dependências necessárias"""
    required = ['playwright', 'loguru', 'httpx']
    optional = ['pandas', 'PyPDF2', 'pdfplumber']
    
    missing_required = []
    missing_optional = []
    
    for dep in required:
        try:
            __import__(dep)
        except ImportError:
            missing_required.append(dep)
    
    for dep in optional:
        try:
            __import__(dep)
        except ImportError:
            missing_optional.append(dep)
    
    if missing_required:
        print(f"❌ Dependências obrigatórias ausentes: {missing_required}")
        print(f"💡 Execute: pip install {' '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"⚠️ Dependências opcionais ausentes: {missing_optional}")
        print(f"💡 Execute: pip install {' '.join(missing_optional)}")
    
    print("✅ Dependências obrigatórias OK")
    return True


# ==================================================================================
# 6. MENU PRINCIPAL
# ==================================================================================

async def main():
    """Menu principal para escolher operação"""
    print("🌟 SISTEMA DJE-SP - SCRIPTS PRÁTICOS")
    print("=" * 50)
    
    if not check_dependencies():
        return
    
    options = {
        "1": ("Extrair data específica", extract_single_date),
        "2": ("Extrair período (múltiplas datas)", run_date_range_extraction),
        "3": ("Gerar relatório analítico", generate_analytics_report),
        "4": ("Exportar para CSV", export_csv),
        "5": ("Sincronizar com API", sync_api),
        "6": ("Teste básico do sistema", run_basic_test),
        "0": ("Sair", None)
    }
    
    while True:
        print(f"\n📋 OPÇÕES DISPONÍVEIS:")
        for key, (description, _) in options.items():
            print(f"   {key}. {description}")
        
        choice = input(f"\n➤ Escolha uma opção: ").strip()
        
        if choice == "0":
            print("👋 Até logo!")
            break
        
        if choice in options:
            description, func = options[choice]
            if func:
                print(f"\n🚀 Executando: {description}")
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func()
                    else:
                        func()
                except KeyboardInterrupt:
                    print(f"\n⏹️ Operação cancelada pelo usuário")
                except Exception as e:
                    print(f"\n❌ Erro: {e}")
                
                input(f"\n⏸️ Pressione Enter para continuar...")
        else:
            print(f"❌ Opção inválida: {choice}")


# ==================================================================================
# FUNÇÕES AUXILIARES DO MENU
# ==================================================================================

async def run_date_range_extraction():
    """Wrapper para extração de período"""
    start_date = input("📅 Data inicial (DD/MM/YYYY): ").strip()
    end_date = input("📅 Data final (DD/MM/YYYY): ").strip()
    
    scraper = AdvancedDateRangeScraper()
    await scraper.extract_date_range(start_date, end_date)

def generate_analytics_report():
    """Wrapper para relatório"""
    analytics = DJEAnalytics()
    analytics.generate_comprehensive_report()

def export_csv():
    """Wrapper para exportação CSV"""
    exporter = DJEExporter()
    output_file = input("📄 Nome do arquivo (deixe vazio para automático): ").strip()
    exporter.export_to_csv(output_file if output_file else None)

async def sync_api():
    """Wrapper para sincronização API"""
    api_url = input("🔗 URL da API: ").strip()
    api_key = input("🔑 API Key: ").strip()
    
    exporter = DJEExporter()
    await exporter.sync_with_api(api_url, api_key)

async def run_basic_test():
    """Teste básico do sistema"""
    print("🧪 Executando teste básico...")
    
    # Teste simples com data atual
    today = datetime.now().strftime("%d/%m/%Y")
    await extract_single_date(today)


# ==================================================================================
# EXECUÇÃO PRINCIPAL
# ==================================================================================

if __name__ == "__main__":
    setup_logging()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n👋 Programa encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)
