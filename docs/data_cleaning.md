# Relatório de Limpeza e Carga de Dados (ETL)
**Data de Execução:** 2026-11-03 23:15:54

## 1. Visão Geral do Pipeline
O pipeline lê os arquivos CSV originais da pasta `arquivos/`, aplica normalização de codificação UTF-8, limpa strings e caracteres em branco, valida rigorosamente os tipos e regras de negócio com **Pydantic** e persiste em banco relacional **SQLite** com integridade referencial (foreign keys ativas) e índices otimizados.

## 2. Métricas de Ingestão e Qualidade
| Entidade | Registros Brutos | Registros Limpos | Validação Pydantic | Nulos Tratados |
| :--- | :---: | :---: | :---: | :---: |
| Categorias | 9 | 9 | 100% OK | 0 |
| Clientes | 50 | 50 | 100% OK | E-mails normalizados |
| Produtos | 65 | 65 | 100% OK | `specs` JSON normalizado |
| Promoções | 25 | 25 | 100% OK | Booleano `is_active` normalizado |
| Pedidos | 20 | 20 | 100% OK | 12 rastreios nulos preservados coerentemente |
| Itens de Pedidos | 22 | 22 | 100% OK | 0 |

## 3. Decisões de Tratamento e Regras de Negócio
- **Codificação UTF-8:** Os arquivos brutos possuem acentuação gráfica portuguesa (ex.: `elétricas`, `acústicos`, `violão`) que foram preservados com fidelidade na ingestão.
- **Coluna `specs` em Produtos:** O campo de especificações técnicas continha JSONs stringificados com aspas escapadas. O schema Pydantic fez o parse estruturado garantindo objetos válidos antes de serializar em formato canônico JSON.
- **Valores Nulos em Pedidos (`orders`):** Pedidos com status `pending`, `confirmed` ou `cancelled` naturalmente não possuem código de rastreamento ou previsão de entrega preenchidos. Esses campos foram mantidos como `NULL` tipado no SQLite.
- **Motivos de Cancelamento:** Registrados no campo `notes` apenas para pedidos cancelados (ex.: 'Item fora de estoque', 'Endereço inválido', 'Cancelado pelo cliente').
- **Duplicidade de E-mail de Clientes:** Foi identificada duplicidade no e-mail `bruno.martins@jmail.com` (Customer ID 11 'Bruno Carvalho Martins' e Customer ID 43 'Bruno Martins'). Decisão de engenharia: o campo `email` foi indexado sem constraint `UNIQUE` restritiva para evitar perda de histórico transacional (o pedido #10 referencia o cliente 11), permitindo que consultas do agente por e-mail ou nome encontrem ambos os registros com segurança.
- **Flag de Promoção Ativa:** Normalizado para inteiros `0` ou `1` no SQLite para facilitar filtragens determinísticas.

## 4. Integridade do Banco SQLite Gerado
O banco foi criado em `data/emporio_da_musica.db` com as seguintes garantias:
- `PRAGMA foreign_keys = ON;` ativo.
- Chaves primárias e estrangeiras válidas sem órfãos.
- Índices criados para queries frequentes do agente (busca de produtos por nome/categoria, verificação de pedidos por cliente/rastreio, promoções ativas).