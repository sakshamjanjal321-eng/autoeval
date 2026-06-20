from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED

from autoeval.loader import TestCase, TestCaseResult, TestSuiteResult

class RichCLIReporter:
    def __init__(self):
        self.console = Console()
        self.live: Optional[Live] = None
        self.results_map: Dict[str, Dict[str, Any]] = {}
        self.models: List[str] = []
        self.tests: List[TestCase] = []
        self.suite_name = ""

    def on_start(self, suite_name: str, models: List[str], test_cases: List[TestCase]):
        self.suite_name = suite_name
        self.models = models
        self.tests = test_cases
        
        self.console.print(Panel(
            Text(f"Starting Benchmark Suite: {suite_name}\nModels: {', '.join(models)}", style="bold cyan", justify="center"),
            box=ROUNDED,
            border_style="cyan"
        ))
        
        # Initialize results map for live table rendering
        for t in test_cases:
            self.results_map[t.name] = {}
            for m in models:
                self.results_map[t.name][m] = {
                    "status": "PENDING",
                    "latency": 0.0,
                    "score": 0.0,
                    "error": None
                }
                
        self.live = Live(self._generate_table(), console=self.console, refresh_per_second=4)
        self.live.start()

    def on_test_start(self, model: str, test_case: TestCase):
        if test_case.name in self.results_map and model in self.results_map[test_case.name]:
            self.results_map[test_case.name][model]["status"] = "RUNNING"
            if self.live:
                self.live.update(self._generate_table())

    def on_test_complete(self, result: TestCaseResult):
        t_name = result.test_case.name
        m_name = result.model
        
        if t_name in self.results_map and m_name in self.results_map[t_name]:
            score = 0.0
            status = "PASS"
            
            if result.response.error:
                status = "ERROR"
                err = result.response.error
            else:
                err = None
                # Aggregate evaluations score (average)
                if result.evaluations:
                    scores = [e.score for e in result.evaluations]
                    score = sum(scores) / len(scores)
                    if any(e.status == "FAIL" for e in result.evaluations):
                        status = "FAIL"
                    elif any(e.status == "ERROR" for e in result.evaluations):
                        status = "ERROR"
                else:
                    score = 1.0  # No evaluators defined, assume pass
                    
            self.results_map[t_name][m_name] = {
                "status": status,
                "latency": result.response.latency,
                "score": score,
                "error": err
            }
            
            if self.live:
                self.live.update(self._generate_table())

    def on_complete(self, suite_result: TestSuiteResult):
        if self.live:
            self.live.stop()
            
        self.console.print("\n")
        self.console.print(Panel(
            Text(f"Benchmark Suite Completed: {self.suite_name}", style="bold green", justify="center"),
            box=ROUNDED,
            border_style="green"
        ))
        
        # Print a beautiful summary table
        summary_table = Table(title="Model Summary Leaderboard", box=ROUNDED, border_style="cyan")
        summary_table.add_column("Model", style="bold white")
        summary_table.add_column("Pass Rate", justify="right")
        summary_table.add_column("Avg Score", justify="right")
        summary_table.add_column("Avg Latency", justify="right")
        summary_table.add_column("Total Cost", justify="right")
        
        # Calculate stats per model
        model_stats = {}
        for m in self.models:
            total_tests = 0
            passed_tests = 0
            total_score = 0.0
            total_latency = 0.0
            total_cost = 0.0
            
            for res in suite_result.results:
                if res.model == m:
                    total_tests += 1
                    total_latency += res.response.latency
                    total_cost += res.response.cost
                    
                    tc_score = 0.0
                    tc_failed = False
                    if res.evaluations:
                        tc_score = sum(e.score for e in res.evaluations) / len(res.evaluations)
                        tc_failed = any(e.status == "FAIL" or e.status == "ERROR" for e in res.evaluations)
                    else:
                        tc_score = 1.0
                        
                    total_score += tc_score
                    if not tc_failed and not res.response.error:
                        passed_tests += 1
                        
            avg_score = (total_score / total_tests) if total_tests > 0 else 0.0
            pass_rate = (passed_tests / total_tests) if total_tests > 0 else 0.0
            avg_latency = (total_latency / total_tests) if total_tests > 0 else 0.0
            
            model_stats[m] = {
                "pass_rate": pass_rate,
                "avg_score": avg_score,
                "avg_latency": avg_latency,
                "total_cost": total_cost
            }
            
        # Sort models by average score descending
        sorted_models = sorted(self.models, key=lambda m: model_stats[m]["avg_score"], reverse=True)
        
        for m in sorted_models:
            stats = model_stats[m]
            summary_table.add_row(
                m,
                f"{stats['pass_rate']*100:.1f}%",
                f"{stats['avg_score']:.2f}",
                f"{stats['avg_latency']:.2f}s",
                f"${stats['total_cost']:.6f}"
            )
            
        self.console.print(summary_table)

    def _generate_table(self) -> Table:
        table = Table(title="Live Benchmark Progress", box=ROUNDED)
        table.add_column("Test Case", style="bold white")
        
        for m in self.models:
            table.add_column(m, justify="center")
            
        for t in self.tests:
            row_data = [t.name]
            for m in self.models:
                cell = self.results_map[t.name][m]
                status = cell["status"]
                
                if status == "PENDING":
                    text = Text("Pending", style="yellow")
                elif status == "RUNNING":
                    text = Text("Running...", style="blue bold")
                elif status == "PASS":
                    text = Text(f"PASS ({cell['score']:.2f})", style="green")
                elif status == "FAIL":
                    text = Text(f"FAIL ({cell['score']:.2f})", style="red")
                elif status == "ERROR":
                    text = Text("ERROR", style="red bold underline")
                else:
                    text = Text(status)
                    
                row_data.append(text)
            table.add_row(*row_data)
            
        return table
