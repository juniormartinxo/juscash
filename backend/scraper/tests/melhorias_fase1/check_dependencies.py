#!/usr/bin/env python3
"""
🔍 VERIFICADOR DE DEPENDÊNCIAS - MELHORIAS FASE 1

Script para verificar se todas as dependências necessárias para as melhorias
estão instaladas e funcionando corretamente.
"""

import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Dict, Any, Tuple


class DependencyChecker:
    """Verificador de dependências para as melhorias do scraper"""

    def __init__(self):
        self.results = {
            "python_version": False,
            "required_packages": {},
            "optional_packages": {},
            "browser_dependencies": {},
            "environment_vars": {},
            "directory_structure": {},
            "overall_status": False,
        }

    def check_all(self) -> Dict[str, Any]:
        """Executa todas as verificações de dependências"""
        print("🔍 VERIFICADOR DE DEPENDÊNCIAS - MELHORIAS FASE 1")
        print("=" * 60)

        # 1. Verificar versão do Python
        self._check_python_version()

        # 2. Verificar pacotes Python obrigatórios
        self._check_required_packages()

        # 3. Verificar pacotes opcionais
        self._check_optional_packages()

        # 4. Verificar dependências do browser
        self._check_browser_dependencies()

        # 5. Verificar variáveis de ambiente
        self._check_environment_variables()

        # 6. Verificar estrutura de diretórios
        self._check_directory_structure()

        # 7. Gerar relatório final
        self._generate_final_report()

        return self.results

    def _check_python_version(self):
        """Verifica se a versão do Python é adequada"""
        print("\n🐍 Verificando versão do Python...")

        version = sys.version_info
        required_major = 3
        required_minor = 8

        if version.major >= required_major and version.minor >= required_minor:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
            self.results["python_version"] = True
        else:
            print(
                f"❌ Python {version.major}.{version.minor}.{version.micro} - Requer Python {required_major}.{required_minor}+"
            )
            self.results["python_version"] = False

    def _check_required_packages(self):
        """Verifica pacotes Python obrigatórios"""
        print("\n📦 Verificando pacotes obrigatórios...")

        required_packages = {
            "playwright": "1.52.0",
            "loguru": "0.7.3",
            "pydantic": "2.11.5",
            "httpx": "0.28.1",
            "beautifulsoup4": "4.13.4",
            "redis": "6.2.0",
            "asyncio": None,  # Built-in
            "pathlib": None,  # Built-in
            "typing": None,  # Built-in
            "re": None,  # Built-in
        }

        for package, expected_version in required_packages.items():
            status = self._check_package(package, expected_version)
            self.results["required_packages"][package] = status

    def _check_optional_packages(self):
        """Verifica pacotes opcionais (para testes)"""
        print("\n📦 Verificando pacotes opcionais...")

        optional_packages = {
            "pytest": "8.4.0",
            "pytest-asyncio": "1.0.0",
            "PyPDF2": "3.0.1",
            "pdfplumber": "0.11.4",
        }

        for package, expected_version in optional_packages.items():
            status = self._check_package(package, expected_version, optional=True)
            self.results["optional_packages"][package] = status

    def _check_package(
        self, package_name: str, expected_version: str = None, optional: bool = False
    ) -> Dict[str, Any]:
        """Verifica um pacote específico"""
        try:
            module = importlib.import_module(package_name)

            # Tentar obter versão
            version = None
            for attr in ["__version__", "version", "VERSION"]:
                if hasattr(module, attr):
                    version = getattr(module, attr)
                    break

            status_icon = "✅" if not optional else "🔵"
            print(f"{status_icon} {package_name} {version or '(versão não detectada)'}")

            return {
                "installed": True,
                "version": version,
                "expected": expected_version,
                "status": "OK",
            }

        except ImportError:
            status_icon = "❌" if not optional else "⚠️"
            print(f"{status_icon} {package_name} - NÃO INSTALADO")

            return {
                "installed": False,
                "version": None,
                "expected": expected_version,
                "status": "MISSING",
            }

    def _check_browser_dependencies(self):
        """Verifica dependências do browser Playwright"""
        print("\n🌐 Verificando dependências do browser...")

        try:
            from playwright.async_api import async_playwright

            print("✅ Playwright importado com sucesso")
            self.results["browser_dependencies"]["playwright"] = True

            # Verificar se browsers estão instalados
            try:
                result = subprocess.run(
                    ["python", "-m", "playwright", "install", "--dry-run"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if "chromium" in result.stdout.lower():
                    print("🔵 Chromium disponível para instalação")
                    self.results["browser_dependencies"]["chromium"] = "available"
                else:
                    print("✅ Chromium já instalado")
                    self.results["browser_dependencies"]["chromium"] = "installed"

            except subprocess.TimeoutExpired:
                print("⚠️ Timeout ao verificar browsers - assumindo OK")
                self.results["browser_dependencies"]["chromium"] = "timeout"

        except ImportError:
            print("❌ Playwright não instalado")
            self.results["browser_dependencies"]["playwright"] = False

    def _check_environment_variables(self):
        """Verifica variáveis de ambiente importantes"""
        print("\n🔧 Verificando variáveis de ambiente...")

        import os

        # Variáveis críticas (podem não estar definidas em ambiente de teste)
        critical_vars = {
            "SCRAPER_TARGET_URL": "https://esaj.tjsp.jus.br/cdje/consultaAvancada.do#buscaavancada",
            "API_BASE_URL": "http://localhost:3001",
        }

        # Variáveis opcionais
        optional_vars = {
            "SCRAPER_MAX_RETRIES": "3",
            "SCRAPER_MAX_PAGES": "20",
            "BROWSER_HEADLESS": "true",
            "TEST_MODE": "true",
        }

        for var, default in critical_vars.items():
            value = os.getenv(var)
            if value:
                print(f"✅ {var} = {value}")
                self.results["environment_vars"][var] = {"set": True, "value": value}
            else:
                print(f"⚠️ {var} - Não definida (usando padrão: {default})")
                self.results["environment_vars"][var] = {
                    "set": False,
                    "default": default,
                }

        for var, default in optional_vars.items():
            value = os.getenv(var)
            if value:
                print(f"🔵 {var} = {value}")
                self.results["environment_vars"][var] = {"set": True, "value": value}
            else:
                print(f"🔵 {var} - Não definida (padrão: {default})")
                self.results["environment_vars"][var] = {
                    "set": False,
                    "default": default,
                }

    def _check_directory_structure(self):
        """Verifica estrutura de diretórios necessária"""
        print("\n📁 Verificando estrutura de diretórios...")

        base_path = Path(__file__).parent.parent.parent

        required_dirs = [
            "src/infrastructure/web",
            "src/domain/entities",
            "src/application/usecases",
            "tests/melhorias_fase1/data_tests",
            "tests/melhorias_fase1/cache",
            "tests/melhorias_fase1/logs",
        ]

        for dir_path in required_dirs:
            full_path = base_path / dir_path
            if full_path.exists():
                print(f"✅ {dir_path}")
                self.results["directory_structure"][dir_path] = True
            else:
                print(f"❌ {dir_path} - FALTANDO")
                self.results["directory_structure"][dir_path] = False

    def _generate_final_report(self):
        """Gera relatório final das verificações"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)

        # Contar sucessos/falhas
        total_checks = 0
        passed_checks = 0

        # Python version
        total_checks += 1
        if self.results["python_version"]:
            passed_checks += 1

        # Required packages
        for package, status in self.results["required_packages"].items():
            total_checks += 1
            if status["installed"]:
                passed_checks += 1

        # Directory structure
        for dir_path, exists in self.results["directory_structure"].items():
            total_checks += 1
            if exists:
                passed_checks += 1

        # Browser dependencies
        if self.results["browser_dependencies"].get("playwright"):
            passed_checks += 1
        total_checks += 1

        success_rate = (passed_checks / total_checks) * 100

        print(
            f"✅ Verificações aprovadas: {passed_checks}/{total_checks} ({success_rate:.1f}%)"
        )

        if success_rate >= 90:
            print("🎉 SISTEMA PRONTO PARA MELHORIAS!")
            self.results["overall_status"] = True
        elif success_rate >= 75:
            print("⚠️ SISTEMA PARCIALMENTE PRONTO - Verificar itens em falta")
            self.results["overall_status"] = False
        else:
            print("❌ SISTEMA NÃO PRONTO - Muitas dependências em falta")
            self.results["overall_status"] = False

        # Próximos passos
        print("\n🎯 PRÓXIMOS PASSOS:")
        if not self.results["overall_status"]:
            print("1. Instalar dependências em falta:")
            print("   pip install -r ../../requirements.txt")
            print("2. Instalar browsers Playwright:")
            print("   python -m playwright install chromium --with-deps")
            print("3. Executar este script novamente")
        else:
            print("1. ✅ Todas as dependências estão OK")
            print("2. 🚀 Pronto para iniciar Fase 2 (Page Manager)")
            print("3. 📋 Usar dados de teste em data_tests/")


def main():
    """Função principal"""
    checker = DependencyChecker()
    results = checker.check_all()

    # Salvar resultados em arquivo
    import json

    results_file = Path(__file__).parent / "dependency_check_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n💾 Resultados salvos em: {results_file}")

    # Exit code baseado no status
    sys.exit(0 if results["overall_status"] else 1)


if __name__ == "__main__":
    main()
