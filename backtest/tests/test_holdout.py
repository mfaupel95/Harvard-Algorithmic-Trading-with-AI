"""Offline regression: execute only audited backtest-construction assignments.

Never import example modules: they run backtests/optimizers at import time.
No third-party packages, network, order functions or production files are used.
"""
import ast
from pathlib import Path
import unittest


BACKTEST = Path(__file__).resolve().parents[1]
SCRIPTS = ("template.py", "bb_squeeze_adx.py")


class Rows(list):
    @property
    def iloc(self):
        return self


class FakeBacktest:
    def __init__(self, data, strategy, **kwargs):
        self.data = data
        self.strategy = strategy
        self.kwargs = kwargs


class HoldoutTests(unittest.TestCase):
    def optimizer_input(self, name, count):
        tree = ast.parse((BACKTEST / name).read_text(encoding="utf-8"))
        scope = {
            "data": Rows(range(count)), "Backtest": FakeBacktest,
            "BBSqueezeADX": object(), "BollingerBandBreakoutShort": object(),
            "KAPITAL": 100000, "KOMMISSION_JE_SEITE": 0.002, "SPREAD": 0.0005,
        }
        # Only these simple assignments can execute; no imports or strategy code.
        assignments = []
        for node in tree.body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in {"bt", "halb", "bt_suche"}):
                assignments.append(node)
        module = ast.Module(body=assignments, type_ignores=[])
        exec(compile(module, name, "exec"), {"__builtins__": {"len": len}}, scope)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "optimize"]
        self.assertEqual(len(calls), 1)
        self.assertIsInstance(calls[0].func.value, ast.Name)
        return scope[calls[0].func.value.id], scope

    def test_optimization_sees_only_first_half(self):
        for name in SCRIPTS:
            for count in (10, 11):
                with self.subTest(script=name, rows=count):
                    optimizer, scope = self.optimizer_input(name, count)
                    half = count // 2
                    self.assertEqual(list(optimizer.data), list(range(half)))
                    self.assertTrue(set(optimizer.data).isdisjoint(range(half, count)))
                    self.assertEqual(list(scope["bt"].data), list(range(count)))

    def test_training_retains_cost_model(self):
        for name in SCRIPTS:
            with self.subTest(script=name):
                optimizer, scope = self.optimizer_input(name, 10)
                self.assertEqual(optimizer.kwargs, scope["bt"].kwargs)
                self.assertEqual(optimizer.kwargs,
                                 {"cash": 100000, "commission": 0.002, "spread": 0.0005})


if __name__ == "__main__":
    unittest.main()
