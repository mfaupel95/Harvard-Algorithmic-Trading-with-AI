"""Prueft die Bedingungen, unter denen die Beispiel-Backtests eine Aussage machen.

Laeuft mit reiner Standardbibliothek: python -m unittest discover -s tests
"""
import unittest
from pathlib import Path

BACKTEST = Path(__file__).resolve().parents[1]
SKRIPTE = ["template.py", "bb_squeeze_adx.py"]
CSV = BACKTEST / "data" / "BTC-6h-1000wks-data.csv"


class BeispielBacktests(unittest.TestCase):
    def test_kein_harter_pfad_mehr(self):
        for name in SKRIPTE:
            text = (BACKTEST / name).read_text(encoding="utf-8")
            self.assertNotIn("/Users/", text, f"{name} traegt wieder einen fremden Absolutpfad")
            self.assertIn("Path(__file__)", text, f"{name} laedt die Daten nicht relativ zur Datei")

    def test_kostenmodell_ist_im_code(self):
        for name in SKRIPTE:
            text = (BACKTEST / name).read_text(encoding="utf-8")
            self.assertIn("KOMMISSION_JE_SEITE = 0.002", text, f"{name} hat keinen Kostensatz")
            self.assertIn("SPREAD = 0.0005", text, f"{name} hat keinen Spread")
            self.assertIn("commission=KOMMISSION_JE_SEITE", text, f"{name} gibt die Kommission nicht an")
            self.assertIn("spread=SPREAD", text, f"{name} gibt den Spread nicht an")
            self.assertIn("kostenkopf", text, f"{name} weist das Ergebnis nicht mit Kostensatz aus")

    def test_kosten_sind_rechenbar(self):
        kommission, spread = 0.002, 0.0005
        self.assertAlmostEqual((kommission + spread) * 2 * 100, 0.5, places=6,
                               msg="Kosten je Runde muessen im Code und in KOSTEN.md gleich sein")

    def test_daten_bestand(self):
        with CSV.open(encoding="utf-8") as f:
            kopf = f.readline().strip().split(",")
            zeilen = sum(1 for _ in f)
        self.assertEqual(kopf, ["datetime", "open", "high", "low", "close", "volume"],
                         "CSV-Kopfzeile hat sich geaendert - die Umbenennung in den Skripten pruefen")
        self.assertEqual(zeilen, 12903, "Kerzenfenster hat sich geaendert - KOSTEN.md nachmessen")

    def test_kosten_doku_liegt_bei(self):
        doku = BACKTEST / "KOSTEN.md"
        self.assertTrue(doku.exists(), "backtest/KOSTEN.md fehlt")
        text = doku.read_text(encoding="utf-8")
        for wert in ("0,0016", "−18,68 %", "−0,197", "0,5 %"):
            self.assertIn(wert, text, f"KOSTEN.md traegt den gemessenen Wert {wert} nicht")


if __name__ == "__main__":
    unittest.main()
