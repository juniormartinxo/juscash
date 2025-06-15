#!/usr/bin/env python3
"""
Script temporário para debugar publicação
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

    print("📋 DADOS ORIGINAIS DA FILA:")
    print("=" * 50)
    for key, value in publication_data.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"{key}: {value[:100]}...")
        else:
            print(f"{key}: {value}")

    print("\n🔄 RECONSTRUINDO PUBLICAÇÃO:")
    print("=" * 50)

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

        print("✅ Publicação reconstruída com sucesso!")
        print(f"   Processo: {publication.process_number}")
        print(f"   Autores: {publication.authors}")
        print(f"   Advogados: {len(publication.lawyers)}")
        print(
            f"   Valores: gross={publication.gross_value}, net={publication.net_value}"
        )

        print("\n📤 DADOS PARA API:")
        print("=" * 50)
        api_data = publication.to_api_dict()
        for key, value in api_data.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"{key}: {value[:100]}...")
            else:
                print(f"{key}: {value}")

    except Exception as e:
        print(f"❌ Erro ao reconstruir publicação: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
