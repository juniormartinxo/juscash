# 🛠️ Guia de Correção - Valores Monetários no Frontend

## ❌ Problema Identificado

Os valores monetários não aparecem no componente `PublicationModal` porque:

1. **Nosso scraper salva** valores como strings no JSON (ex: `"1242337"`)
2. **Frontend espera** BigInt serializado da API ou formato específico
3. **Função `formatCurrency`** não estava lidando com strings numéricas

## ✅ Soluções Implementadas

### 1. **Backend - ReportJsonSaver Corrigido**

Agora salvamos valores como strings (compatível com API):

```python
# ANTES (causava problema)
"gross_value": publication.gross_value.amount_cents if publication.gross_value else 0

# AGORA (corrigido)
"gross_value": str(publication.gross_value.amount_cents) if publication.gross_value else None
```

### 2. **Frontend - Função formatCurrency Melhorada**

Substitua a função em `frontend/src/lib/utils.ts`:

```typescript
// Versão melhorada da função formatCurrency
export function formatCurrency(value: any): string {
    if (value === null || value === undefined) return 'N/A'

    try {
        let numericValue: number;

        // Se for um objeto superjson (vem da API), deserializar
        if (value && typeof value === 'object' && value.json !== undefined && value.meta !== undefined) {
            const deserializedValue = superjson.deserialize(value)
            numericValue = typeof deserializedValue === 'bigint' 
                ? Number(deserializedValue) 
                : Number(deserializedValue)
        }
        // Se for string (vem dos JSONs diretos do scraper), converter para número
        else if (typeof value === 'string') {
            numericValue = parseInt(value, 10)
        }
        // Se for número direto
        else if (typeof value === 'number') {
            numericValue = value
        }
        // Se for BigInt direto
        else if (typeof value === 'bigint') {
            numericValue = Number(value)
        }
        else {
            console.warn('Formato de valor monetário não reconhecido:', typeof value, value)
            return 'N/A'
        }

        // Verificar se é um número válido
        if (!Number.isFinite(numericValue) || isNaN(numericValue)) {
            console.warn('Valor monetário inválido:', numericValue)
            return 'N/A'
        }

        // Formatar como moeda brasileira (valor já está em centavos)
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(numericValue / 100)
        
    } catch (error) {
        console.warn('Erro ao formatar currency:', error, 'Value:', value)
        return 'N/A'
    }
}
```

## 🧪 Como Testar

### 1. **Testar Backend (valores no JSON)**

```bash
cd backend/scraper
python test-monetary-values.py
```

**Saída esperada:**

```
🧪 Testando valores monetários no JSON
📄 Publicação de teste criada: 0003901-40.2025.8.26.0053
💰 Valor bruto: R$ 12423.37
💰 Valor líquido: R$ 12423.37
💰 Juros: R$ 8089.05
💰 Honorários: R$ 2159.76

📋 Dados salvos no JSON:
   gross_value: 1242337 (tipo: <class 'str'>)
   net_value: 1242337 (tipo: <class 'str'>)
   interest_value: 808905 (tipo: <class 'str'>)
   attorney_fees: 215976 (tipo: <class 'str'>)

🌐 Como o frontend interpretaria:
   Bruto: R$ 12.423,37
   Líquido: R$ 12.423,37
   Juros: R$ 8.089,05
   Honorários: R$ 2.159,76

✅ Teste concluído!
```

### 2. **Testar Frontend**

Após aplicar a correção no `utils.ts`, os valores devem aparecer corretamente no `PublicationModal`.

## 📁 Arquivos para Alterar

### `frontend/src/lib/utils.ts`

Substitua a função `formatCurrency` existente pela versão melhorada acima.

## 🔍 Formato dos Valores

### **Nos JSONs do Scraper:**

```json
{
  "gross_value": "1242337",
  "net_value": "1242337", 
  "interest_value": "808905",
  "attorney_fees": "215976"
}
```

### **Da API (com superjson):**

```json
{
  "gross_value": {
    "json": "1242337",
    "meta": {"values": {"gross_value": ["bigint"]}}
  }
}
```

### **No Frontend (após formatCurrency):**

- `gross_value: "1242337"` → `"R$ 12.423,37"`
- `interest_value: "808905"` → `"R$ 8.089,05"`
- `attorney_fees: "215976"` → `"R$ 2.159,76"`

## ✅ Resultado Final

Com essas correções:

1. ✅ **JSONs do scraper** salvam valores como strings
2. ✅ **Função formatCurrency** lida com strings, numbers, BigInt e superjson
3. ✅ **PublicationModal** mostra valores corretamente
4. ✅ **Compatibilidade** mantida com API existente

## 🚨 Importante

- **Valores estão em centavos** nos JSONs (ex: 1242337 = R$ 12.423,37)
- **Função formatCurrency divide por 100** para exibir corretamente
- **Strings são convertidas** para números antes da formatação
- **Fallbacks** implementados para casos de erro
