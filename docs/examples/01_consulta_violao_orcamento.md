# Exemplo 1: Consulta de Violões por Orçamento (Até R$ 1.000)

**Cenário:** Cliente com orçamento limitado procurando violões disponíveis na loja por até R$ 1.000,00.  
**Desafio / Pegadinha:** O banco de dados possui o *Giannini GF-3D* com estoque zerado (`stock_quantity = 0`) e o *Shelby SN-7C* descontinuado (`status = 'discontinued'`). O agente deve filtrar e apresentar apenas instrumentos ativos e em estoque, sem alucinar modelos indisponíveis.

---

### Diálogo

**Usuário:**
> Olá! Estou procurando um violão para começar a estudar, mas meu orçamento é de no máximo R$ 1.000. Vocês têm opções disponíveis nessa faixa de preço?

**Agente (Pensamento Interno / ReAct):**
- *Ferramenta identificada:* `search_products(query="violão", max_price=1000.0, available_only=True)`
- *Saída da Ferramenta:*
  - `[ID 83] Tagima Memphis AC-39 Nylon Natural (Violões) | R$ 429,90 (ou R$ 408,41 no PIX) | Estoque: 15 un. | Status: active`
  - `[ID 87] Michael Taurus VM681DT Folk Aço Natural (Violões) | R$ 899,00 (ou R$ 854,05 no PIX) | Estoque: 8 un. | Status: active`
- *Verificação de Guardrail:* Excluiu com sucesso o Giannini GF-3D (sem estoque) e o Shelby SN-7C (descontinuado).

**Agente (Resposta ao Cliente):**
> Olá! Seja muito bem-vindo à **Empório da Música**! 🎶
> 
> Temos excelentes opções para você começar os seus estudos com qualidade e sem estourar o seu orçamento de R$ 1.000,00:
> 
> 1. **Tagima Memphis AC-39 Clássico Nylon Natural** (ID 83)  
>    - **Preço de Tabela:** R$ 429,90  
>    - **No PIX (5% OFF):** R$ 408,41  
>    - **Condição:** Em até 10x sem juros de R$ 42,99  
>    - **Estoque:** 15 unidades disponíveis  
>    - *Indicação:* Cordas de nylon macias, excelente ergonomia para quem está dando os primeiros acordes.
> 
> 2. **Michael Taurus VM681DT Folk Aço Natural** (ID 87)  
>    - **Preço de Tabela:** R$ 899,00  
>    - **No PIX (5% OFF):** R$ 854,05  
>    - **Condição:** Em até 10x sem juros de R$ 89,90  
>    - **Estoque:** 8 unidades disponíveis  
>    - *Indicação:* Timbre encorpado e brilhante com cordas de aço, ótimo para ritmos de pop, sertanejo e rock.
> 
> Todos os nossos instrumentos acompanham nota fiscal e garantia oficial do fabricante. Gostaria de mais detalhes sobre as especificações de algum deles ou prefere que eu reserve uma unidade para você?

