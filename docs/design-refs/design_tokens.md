# Diretrizes de Design e Tokens Visuais — Empório da Música

Este documento consolida as regras visuais do frontend (`Next.js App Router + Tailwind + shadcn/ui + Lucide`) e as referências extraídas dos 4 templates do Figma Community.

---

## 1. Referências de Arquitetura Visual (Figma Community)

1. **Horizon AI Template (`dk83mrV52Yn00K6G9Kgszm`):**
   - Estrutura em duas colunas: Sidebar lateral fixa (`280px`) + Canvas de chat fluido.
   - Header superior translúcido com pílulas suaves indicando o status do agente, modelo ativo e localização (`Campo Grande/MS`).
   - Composer inferior em card flutuante com botão de envio em formato de **pílula escura**.
2. **ChatGPT v4.5 (`TvH31vazm7NST2kItAJuUq`):**
   - *Empty State* centralizado com boas-vindas e grade 2x2 de cartões de sugestões clicáveis.
3. **AI Chat App UI (`vFkbZ05vsgwLOKzrXUjS1s`):**
   - Rastreabilidade de execução: exibição de **chips em pílulas suaves** acima da resposta do assistente para cada tool MCP acionada (`tool_start` -> `tool_end`).
4. **AI Chat Template (`hy6HcFy02pxo4h5v34UQyu`):**
   - Painel contextual na sidebar com destaques de ofertas ativas da loja e informações rápidas de atendimento.

---

## 2. Paleta de Cores e Superfícies

| Token Semântico | Hexadecimal | Classe Tailwind | Aplicação |
| :--- | :---: | :--- | :--- |
| **Fundo Principal (Creme)** | `#FAF8F5` | `bg-[#FAF8F5]` | Fundo geral da página e área de mensagens |
| **Fundo Sidebar (Creme Quente)** | `#F3EFE6` | `bg-[#F3EFE6]` | Barra lateral esquerda e áreas secundárias |
| **Superfície de Card** | `#FFFFFF` | `bg-white` | Cards de sugestão, balões do assistente e composer |
| **Borda Sutil Quente** | `#E7E2D8` | `border-[#E7E2D8]` | Contorno de cards, divisores e inputs |
| **Acento Âmbar Principal** | `#D97706` | `text-[#D97706]` / `bg-[#D97706]` | Destaques ativos, ícones principais, foco e promoções |
| **Acento Âmbar Suave (Pílula)** | `#FEF3C7` | `bg-[#FEF3C7] text-[#92400E]` | Pílulas de status, chips de tools e descontos |
| **Botão Pílula Escura** | `#1C1917` | `bg-[#1C1917] text-[#FAF8F5]` | Botão principal de enviar mensagem e ações primárias |
| **Texto Primário** | `#1C1917` | `text-[#1C1917]` | Títulos, corpo de texto principal e valor inteiro em R$ |
| **Texto Secundário** | `#57534E` | `text-[#57534E]` | Subtítulos, descrições e metadados |
| **Centavos em Cinza** | `#A8A29E` | `text-[#A8A29E]` | Parte decimal de valores monetários (ex: `,00`, `,90`) |

---

## 3. Geometria, Tipografia e Regras Estritas

- **Raio dos Cards:** Todos os cards principais utilizam **`border-radius: 20px`** (`rounded-[20px]`).
- **Botões e Status:** Formato de **pílula completa** (`rounded-full`).
- **Tipografia:** `Inter` / `Geist Sans` para leitura limpa e `Geist Mono` para códigos de rastreio (`BR...BR`), protocolos (`EMP-...`) e IDs.
- **Ícones:** Exclusivamente `lucide-react` com **traço fino (`strokeWidth={1.5}`)**.
- **Proibição de Emojis:** É estritamente proibido o uso de emojis como ícones de interface ou em cabeçalhos.
- **Tipografia de Preços (Centavos em Cinza):** Valores em Reais (`R$ 2.199,00`) destacam o valor principal em `#1C1917` (`font-semibold`) e estilizam os centavos `,00` em cinza `#A8A29E` (`font-normal text-[0.88em]`).

