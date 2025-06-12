#!/usr/bin/env python3
"""
Verifica se as implementações dos adaptadores estão corretas.
"""
import inspect
from abc import ABC
from typing import get_type_hints

# Importar as interfaces
from src.core.ports.cache_port import CachePort
from src.core.ports.scheduler_port import SchedulerPort

# Importar as implementações
from src.adapters.secondary.redis_cache import RedisCacheAdapter
from src.adapters.primary.scheduler_adapter import APSchedulerAdapter


def get_abstract_methods(cls):
    """Retorna todos os métodos abstratos de uma classe."""
    abstract_methods = set()
    
    for name, value in inspect.getmembers(cls):
        if getattr(value, '__isabstractmethod__', False):
            abstract_methods.add(name)
    
    return abstract_methods


def check_implementation(interface_cls, implementation_cls):
    """Verifica se uma implementação satisfaz uma interface."""
    print(f"\n🔍 Verificando {implementation_cls.__name__} implementa {interface_cls.__name__}")
    
    # Obter métodos abstratos da interface
    abstract_methods = get_abstract_methods(interface_cls)
    
    # Verificar cada método abstrato
    missing_methods = []
    implemented_methods = []
    
    for method_name in abstract_methods:
        if hasattr(implementation_cls, method_name):
            implemented_methods.append(method_name)
        else:
            missing_methods.append(method_name)
    
    # Mostrar resultados
    if implemented_methods:
        print(f"✅ Métodos implementados: {', '.join(implemented_methods)}")
    
    if missing_methods:
        print(f"❌ Métodos faltando: {', '.join(missing_methods)}")
    else:
        print("✅ Todos os métodos foram implementados!")
    
    return len(missing_methods) == 0


def main():
    """Função principal."""
    print("=== Verificação de Interfaces ===")
    
    # Verificar RedisCacheAdapter
    cache_ok = check_implementation(CachePort, RedisCacheAdapter)
    
    # Verificar APSchedulerAdapter
    scheduler_ok = check_implementation(SchedulerPort, APSchedulerAdapter)
    
    print("\n=== Resumo ===")
    if cache_ok and scheduler_ok:
        print("✅ Todas as implementações estão corretas!")
        return 0
    else:
        print("❌ Algumas implementações precisam de correção!")
        return 1


if __name__ == "__main__":
    exit(main())