"""Runner do framework de avaliação automatizada (Evals) do Empório da Música.

Executa a suíte de casos de teste definida em evals/cases.yaml contra o agente ReAct,
validando seleção de ferramentas, cumprimento de guardrails (palavras obrigatórias e proibidas)
e tempo de resposta.
"""

import os
import re
import sys
import time
import unicodedata
import uuid
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Garantir que src esteja no PYTHONPATH e stdout suporte utf-8
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.agent.orchestrator import EmporioMusicAgent


@dataclass
class EvalResult:
    case_id: str
    name: str
    passed: bool
    tool_check_passed: bool
    required_check_passed: bool
    forbidden_check_passed: bool
    expected_tools: List[str]
    actual_tools: List[str]
    missing_required: List[str] = field(default_factory=list)
    found_forbidden: List[str] = field(default_factory=list)
    latency_sec: float = 0.0
    agent_response: str = ""


class EvalSuiteRunner:
    def __init__(self, cases_path: Path):
        self.cases_path = cases_path
        self.cases = self._load_cases()
        self.agent = EmporioMusicAgent()

    def _load_cases(self) -> List[Dict[str, Any]]:
        if not self.cases_path.exists():
            raise FileNotFoundError(f"Arquivo de casos não encontrado: {self.cases_path}")
        with open(self.cases_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("cases", [])

    def run_case(self, case: Dict[str, Any]) -> EvalResult:
        case_id = case["id"]
        name = case.get("name", case_id)
        prompt = case["prompt"]
        expected_tools = case.get("expected_tools", [])
        required_keywords = case.get("required_keywords", [])
        forbidden_keywords = case.get("forbidden_keywords", [])

        thread_id = f"eval-{case_id}-{uuid.uuid4().hex[:6]}"

        start_time = time.perf_counter()
        turn_response = self.agent.run_turn(user_message=prompt, thread_id=thread_id)
        latency = time.perf_counter() - start_time

        actual_tools = [step.tool_name for step in turn_response.tool_calls]
        full_text = turn_response.reply

        # 1. Validação de ferramentas esperadas
        if expected_tools:
            tool_check = all(t in actual_tools for t in expected_tools)
        else:
            # Caso fora de escopo não deve chamar ferramentas de negócio
            tool_check = len(actual_tools) == 0

        # 2. Validação de termos obrigatórios (com normalização NFKC para tratar hífens e espaços tipográficos)
        text_norm = unicodedata.normalize("NFKC", full_text).lower()
        # Normalizar qualquer variante de hífen Unicode para o hífen padrão ASCII
        text_norm = text_norm.replace("\u2011", "-").replace("‑", "-").replace("–", "-").replace("—", "-")
        missing_req = []
        for req in required_keywords:
            alternatives = [unicodedata.normalize("NFKC", alt).strip().lower() for alt in req.split("|")]
            found = False
            for alt in alternatives:
                alt_norm = alt.replace("\u2011", "-").replace("‑", "-")
                if alt_norm in text_norm or alt_norm.replace("-", "") in text_norm.replace("-", ""):
                    found = True
                    break
                # Se for número, checar também removendo espaços/pontos internos (ex: '2 199' vs '2199')
                alt_digits = "".join(c for c in alt if c.isdigit())
                text_digits = "".join(c for c in text_norm if c.isdigit() or c in (" ", ".", ","))
                if alt_digits and alt_digits in text_digits.replace(" ", "").replace(".", ""):
                    found = True
                    break
            if not found:
                missing_req.append(req)
        required_check = len(missing_req) == 0

        # 3. Validação de termos proibidos (case-insensitive, ignorando quando precedido por negação)
        found_forb = []
        for forb in forbidden_keywords:
            forb_clean = unicodedata.normalize("NFKC", forb).lower()
            matches = list(re.finditer(re.escape(forb_clean), text_norm))
            for m in matches:
                start = m.start()
                preceding = text_norm[max(0, start - 15):start]
                if "não " in preceding or "nao " in preceding or "nunca " in preceding or "sem " in preceding:
                    continue
                found_forb.append(forb)
                break
        forbidden_check = len(found_forb) == 0

        passed = tool_check and required_check and forbidden_check

        return EvalResult(
            case_id=case_id,
            name=name,
            passed=passed,
            tool_check_passed=tool_check,
            required_check_passed=required_check,
            forbidden_check_passed=forbidden_check,
            expected_tools=expected_tools,
            actual_tools=actual_tools,
            missing_required=missing_req,
            found_forbidden=found_forb,
            latency_sec=round(latency, 2),
            agent_response=full_text,
        )

    def run_all(self) -> List[EvalResult]:
        results: List[EvalResult] = []
        print(f"\n=======================================================")
        print(f"  Iniciando Avaliação Automatizada do Empório da Música")
        print(f"  Total de casos carregados: {len(self.cases)}")
        print(f"=======================================================\n")

        for idx, case in enumerate(self.cases, 1):
            print(f"[{idx}/{len(self.cases)}] Avaliando: {case['name']}...", end=" ", flush=True)
            res = self.run_case(case)
            status_tag = "PASS" if res.passed else "FAIL"
            print(f"[{status_tag}] ({res.latency_sec}s)")
            results.append(res)
            time.sleep(2.0)

        self._print_summary_table(results)
        return results

    def _print_summary_table(self, results: List[EvalResult]):
        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        avg_latency = sum(r.latency_sec for r in results) / total if total > 0 else 0

        print("\n" + "=" * 90)
        print(f"{'CASO':<32} | {'FERRAMENTA':<12} | {'TERMOS':<10} | {'LATÊNCIA':<8} | {'STATUS'}")
        print("-" * 90)

        for r in results:
            tool_str = "OK" if r.tool_check_passed else "ERR"
            terms_str = "OK" if (r.required_check_passed and r.forbidden_check_passed) else "ERR"
            status_str = "[OK] PASS" if r.passed else "[X] FAIL"
            name_trunc = (r.name[:29] + "...") if len(r.name) > 32 else r.name
            print(f"{name_trunc:<32} | {tool_str:<12} | {terms_str:<10} | {r.latency_sec:>6.2f}s | {status_str}")

        print("=" * 90)
        pass_rate = (passed_count / total) * 100 if total > 0 else 0
        print(f"Taxa de Sucesso: {passed_count}/{total} ({pass_rate:.1f}%) | Latência Média: {avg_latency:.2f}s\n")

        # Exibir detalhes de falhas se houver
        failures = [r for r in results if not r.passed]
        if failures:
            print("Detalhes das falhas encontradas:")
            for f in failures:
                print(f"\n-> Caso: {f.name} ({f.case_id})")
                if not f.tool_check_passed:
                    print(f"   Ferramentas esperadas: {f.expected_tools} | Chamadas: {f.actual_tools}")
                if f.missing_required:
                    print(f"   Termos obrigatórios ausentes: {f.missing_required}")
                if f.found_forbidden:
                    print(f"   Termos proibidos presentes: {f.found_forbidden}")
                print(f"   Resposta do Agente: {f.agent_response[:200]}...")


def main():
    cases_file = PROJECT_ROOT / "evals" / "cases.yaml"
    runner = EvalSuiteRunner(cases_file)
    results = runner.run_all()

    all_passed = all(r.passed for r in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
