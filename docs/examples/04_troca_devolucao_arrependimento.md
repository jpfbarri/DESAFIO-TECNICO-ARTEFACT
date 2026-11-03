# Exemplo 4: Troca, Devolução e Direito de Arrependimento (RAG)

**Cenário:** Cliente comprou um instrumento pelo site, recebeu há 3 dias e deseja devolver por arrependimento, perguntando sobre prazos e custo do frete reverso.  
**Desafio / Pegadinha:** Consulta precisa ao PDF de Políticas da Loja via RAG. Conforme o Artigo 49 do CDC e a Seção 4 do documento, devoluções por arrependimento devem ser solicitadas em até **7 dias corridos** após o recebimento, e o **frete de devolução é arcado integralmente pela Empório da Música** (logística reversa sem custo ao comprador).

---

### Diálogo

**Usuário:**
> Comprei um teclado pelo site de vocês e recebi faz 3 dias, mas achei as teclas muito pesadas para o meu estilo. Posso devolver por arrependimento? Quem paga o frete para mandar de volta?

**Agente (Pensamento Interno / ReAct):**
- *Ferramenta identificada:* `search_policies(query="devolução arrependimento prazo frete compras online")`
- *Trecho recuperado do RAG:*
  - `Seção 4: Devolução por Arrependimento (Compras Online)`
  - *Regra:* 7 dias corridos a partir da data de entrega para compras realizadas fora do estabelecimento físico.
  - *Condições:* Produto na embalagem original, sem sinais de mau uso, acompanhado de nota fiscal e todos os acessórios.
  - *Frete Reverso:* Sem custo para o cliente. A loja emite a autorização de postagem ou agenda a coleta.
  - *Estorno:* 100% do valor pago (incluindo o frete original da compra).

**Agente (Resposta ao Cliente):**
> Olá! Sim, você tem todo o direito de devolver o teclado! 🤝
> 
> De acordo com as nossas **Políticas Oficiais de Troca e Devolução** (e conforme o Artigo 49 do Código de Defesa do Consumidor):
> 
> 1. **Prazo de Arrependimento:** Você tem até **7 dias corridos** após o recebimento do instrumento para solicitar a devolução por arrependimento. Como você recebeu há apenas 3 dias, está perfeitamente dentro do prazo!
> 
> 2. **Custo do Frete de Devolução:** O frete de devolução é **100% por conta da Empório da Música**. Nós geramos uma Autorização de Postagem sem qualquer custo para você levar o pacote aos Correios ou agendamos a coleta da transportadora.
> 
> 3. **Requisitos:** O teclado precisa estar na embalagem original, sem marcas de uso, com manuais, fonte de alimentação e acompanhado da Nota Fiscal.
> 
> 4. **Reembolso:** Após o instrumento chegar à nossa matriz em Campo Grande e passar por uma rápida conferência técnica (até 3 dias úteis), realizamos o estorno integral do valor pago, inclusive do frete original.
> 
> Gostaria que eu abra o seu protocolo de devolução agora mesmo? Se sim, por favor me informe o número do seu pedido e o seu e-mail cadastrado!

