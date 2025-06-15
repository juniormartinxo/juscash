#!/usr/bin/env python3
"""
Script para debugar requisições da API
"""

import sys
import os
import json
import redis
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.insert(0, "/app/src")

from domain.entities.publication import Publication, Lawyer, MonetaryValue


def main():
    # Conectar ao Redis
    r = redis.Redis(
        host="juscash-redis",
        port=6379,
        password="do1HDF1uT5lC49VHuD2xom",
        decode_responses=True,
    )

    # Pegar uma publicação da fila
    pub_data = r.lindex("publications_queue", 0)
    if not pub_data:
        print("❌ Nenhuma publicação na fila")
        return

    publication_data = json.loads(pub_data)

    # Reconstituir publication_date
    publication_date = None
    if publication_data.get("publication_date"):
        publication_date = datetime.fromisoformat(publication_data["publication_date"])

    # Reconstituir availability_date (obrigatório)
    availability_date = datetime.now()
    if publication_data.get("availability_date"):
        availability_date = datetime.fromisoformat(
            publication_data["availability_date"]
        )

    # Reconstituir lawyers
    lawyers = []
    for lawyer_data in publication_data.get("lawyers", []):
        if isinstance(lawyer_data, dict):
            lawyers.append(
                Lawyer(
                    name=lawyer_data.get("name", ""),
                    oab=lawyer_data.get("oab", ""),
                )
            )
        elif isinstance(lawyer_data, str):
            # Formato string simples
            lawyers.append(Lawyer(name=lawyer_data, oab=""))

    # Reconstituir valores monetários
    gross_value = None
    net_value = None
    interest_value = None
    attorney_fees = None

    monetary_values = publication_data.get("monetary_values", [])
    for mv_data in monetary_values:
        if isinstance(mv_data, dict):
            amount_cents = mv_data.get("value", 0)
            mv_type = mv_data.get("type", "").lower()

            if "honorario" in mv_type or "attorney" in mv_type:
                attorney_fees = MonetaryValue(amount_cents=amount_cents)
            elif "juros" in mv_type or "interest" in mv_type:
                interest_value = MonetaryValue(amount_cents=amount_cents)
            elif "bruto" in mv_type or "gross" in mv_type:
                gross_value = MonetaryValue(amount_cents=amount_cents)
            elif "liquido" in mv_type or "net" in mv_type:
                net_value = MonetaryValue(amount_cents=amount_cents)

    # Criar Publication
    try:
        publication = Publication(
            process_number=publication_data["process_number"],
            publication_date=publication_date,
            availability_date=availability_date,
            authors=publication_data.get("authors", []),
            lawyers=lawyers,
            gross_value=gross_value,
            net_value=net_value,
            interest_value=interest_value,
            attorney_fees=attorney_fees,
            content=publication_data.get("content", ""),
            extraction_metadata=publication_data.get("metadata", {}),
        )

        # Gerar JSON exato que seria enviado
        api_data = publication.to_api_dict()
        json_payload = json.dumps(api_data, ensure_ascii=False, indent=2)

        print("📤 JSON EXATO QUE SERIA ENVIADO:")
        print("=" * 50)
        print(json_payload)

        print("\n🔍 ANÁLISE DE CARACTERES:")
        print("=" * 50)
        for key, value in api_data.items():
            if isinstance(value, str):
                print(f"{key}: {len(value)} chars")
                # Verificar caracteres especiais
                non_ascii = [c for c in value if ord(c) > 127]
                if non_ascii:
                    print(f"  ⚠️  Caracteres não-ASCII: {non_ascii}")
            elif isinstance(value, list) and value and isinstance(value[0], str):
                for i, item in enumerate(value):
                    print(f"{key}[{i}]: {len(item)} chars")
                    non_ascii = [c for c in item if ord(c) > 127]
                    if non_ascii:
                        print(f"  ⚠️  Caracteres não-ASCII: {non_ascii}")

    except Exception as e:
        print(f"❌ Erro ao reconstruir publicação: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
