import argparse
import sys
from uuid import uuid4

import uvicorn

from src.agent.orchestrator import EmporioMusicAgent
from src.database.connection import get_db_path
from src.etl.clean_and_load import run_etl

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000


def ensure_database_ready() -> None:
    db_path = get_db_path()
    if not db_path.exists():
        run_etl()


def run_interactive_cli() -> None:
    ensure_database_ready()
    agent = EmporioMusicAgent()
    thread_id = f"cli-{uuid4().hex[:8]}"
    print("=" * 65)
    print("🎸 EMPÓRIO DA MÚSICA — Assistente Virtual (Campo Grande/MS)")
    print(f"Sessão: {thread_id} | Digite 'sair' para encerrar ou 'limpar' para nova conversa.")
    print("=" * 65)

    while True:
        try:
            user_input = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo! 🎶")
            break
        if not user_input:
            continue
        if user_input.lower() in ("sair", "exit", "quit"):
            print("Encerrando atendimento. Sua música começa aqui! 🎶")
            break
        if user_input.lower() in ("limpar", "reset", "nova"):
            agent.checkpointer.clear_thread(thread_id)
            print("[Memória da conversa reiniciada]")
            continue

        turn = agent.run_turn(user_message=user_input, thread_id=thread_id)
        if turn.tool_calls:
            tools_str = ", ".join(
                f"{t.tool_name}({t.arguments})" for t in turn.tool_calls
            )
            print(f"\n[🔧 Tools acionadas: {tools_str}]")
        print(f"\nEmpório da Música:\n{turn.reply}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Empório da Música — AI Support Agent")
    parser.add_argument("--cli", action="store_true", help="Inicia o chat interativo no terminal")
    parser.add_argument("--etl", action="store_true", help="Executa o pipeline de ETL e validação")
    parser.add_argument("--server", action="store_true", help="Inicia o servidor FastAPI (padrão)")
    parser.add_argument("--port", type=int, default=DEFAULT_API_PORT, help="Porta da API FastAPI")
    args = parser.parse_args()

    if args.etl:
        run_etl()
        return
    if args.cli:
        run_interactive_cli()
        return

    ensure_database_ready()
    uvicorn.run("src.api.app:app", host=DEFAULT_API_HOST, port=args.port, reload=True)


if __name__ == "__main__":
    main()

