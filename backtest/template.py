import numpy as np
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from pathlib import Path

# Datenpfad relativ zur Datei, nicht haarverfilzt auf ein anderes Betriebssystem.
DATA = Path(__file__).resolve().parent / "data" / "BTC-6h-1000wks-data.csv"
KAPITAL = 100000

# Kostenmodell: ohne diese Angaben ist kein Ergebnis eine Aussage.
# KOMMISSION_JE_SEITE = 0.002 ist der hardcodierte Default des Upstream-Repos, KEINE
# Messung. OKX erhebt fuer Futures regulär 0,05 % Taker / 0,02 % Maker (okx.com,
# Trading Fee Rules) - dieser Satz liegt also 4x ueber dem realen Taker-Satz und ist
# bewusst konservativ. Beide Saetze sind in backtest/KOSTEN.md gegenübergestellt,
# samt Auswirkung auf das Ergebnis.
KOMMISSION_JE_SEITE = 0.002  # 0,2 % je Seite, konservativ
SPREAD = 0.0005              # 5 Basispunkte je Seite

data = pd.read_csv(DATA, parse_dates=['datetime'], index_col='datetime')

# Bollinger Band Breakout Strategy (Short Only)
class BollingerBandBreakoutShort(Strategy):
    window = 21
    num_std = 2.7
    take_profit = 0.05  # 5%
    stop_loss = 0.03    # 3%

    def init(self):
        # Calculate Bollinger Bands using TA-Lib
        self.upper_band, self.middle_band, self.lower_band = self.I(talib.BBANDS, self.data.Close, self.window, self.num_std, self.num_std)

    def next(self):
        if len(self.data) < self.window:
            return

        # Check for breakout below lower band
        if self.data.Close[-1] < self.lower_band[-1] and not self.position:
            self.sell(sl=self.data.Close[-1] * (1 + self.stop_loss),
                      tp=self.data.Close[-1] * (1 - self.take_profit))

# Ensure necessary columns are present and rename correctly
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']


def kostenkopf(titel, st):
    """Ergebnis mit Kostensatz: Gebuehr je Seite, Spread, Anzahl Runden, netto je Runde."""
    runden = int(st['# Trades'])
    kosten = (KOMMISSION_JE_SEITE + SPREAD) * 2 * 100
    netto = (st['Equity Final [$]'] - KAPITAL) / KAPITAL / runden * 100 if runden else float('nan')
    print(f"{titel}: {st['Return [%]']:.2f} % | {runden} Runden | "
          f"Kosten {kosten:.2f} % je Runde | netto {netto:.3f} % je Runde | "
          f"Max. Drawdown {st['Max. Drawdown [%]']:.2f} %")


# Create and configure the backtest
bt = Backtest(data, BollingerBandBreakoutShort, cash=KAPITAL,
              commission=KOMMISSION_JE_SEITE, spread=SPREAD)

# Run the backtest with default parameters and print the results
stats_default = bt.run()
print("Default Parameters Results:")
print(stats_default)
kostenkopf('Standard-Parameter', stats_default)

# Trennung von Suchfenster und Prueffenster. Der Optimierer weiter unten sucht im
# Ganzen, deshalb wird hier zusaetzlich geteilt gerechnet: ohne diese Zeile ist
# das Optimierungsergebnis der groesste Wert einer Suche, kein Beweis.
halb = len(data) // 2
for name, teil in (('Suchfenster (erste Haelfte)', data.iloc[:halb]),
                   ('Prueffenster (zweite Haelfte)', data.iloc[halb:])):
    st = Backtest(teil, BollingerBandBreakoutShort, cash=KAPITAL,
                  commission=KOMMISSION_JE_SEITE, spread=SPREAD).run()
    kostenkopf(name, st)

# Now perform the optimization
trials = (len(range(10, 20, 5)) * len(np.arange(1.5, 3.5, 0.1))
          * len(range(1, 7, 1)) * len(range(1, 7, 1)))
print(f"\nParameter-Suche: {trials} Kombinationen. Der groesste Wert dieser Menge ist"
      f" das Ergebnis - die Zahl der Versuche gehoert zur Aussage.")

optimization_results = bt.optimize(
    window=range(10, 20, 5),
    num_std=[round(i, 1) for i in np.arange(1.5, 3.5, 0.1)],
    take_profit=[i / 100 for i in range(1, 7, 1)],  # Optimize TP from 1% to 9%
    stop_loss=[i / 100 for i in range(1, 7, 1)],    # Optimize SL from 1% to 9%
    maximize='Equity Final [$]',
    constraint=lambda param: param.window > 0 and param.num_std > 0  # Ensure valid parameters
)

# Print the optimization results
print(optimization_results)

# Print the best optimized values
print("Best Parameters:")
print("Window:", optimization_results._strategy.window)
print("Number of Standard Deviations:", optimization_results._strategy.num_std)
print("Take Profit:", optimization_results._strategy.take_profit)
print("Stop Loss:", optimization_results._strategy.stop_loss)

# Dieselbe Kombination auf dem Prueffenster: traegt der Fund ueber die Haelften?
for k in ('window', 'num_std', 'take_profit', 'stop_loss'):
    setattr(BollingerBandBreakoutShort, k, getattr(optimization_results._strategy, k))
for name, teil in (('Suchfenster', data.iloc[:halb]), ('Prueffenster', data.iloc[halb:])):
    st = Backtest(teil, BollingerBandBreakoutShort, cash=KAPITAL,
                  commission=KOMMISSION_JE_SEITE, spread=SPREAD).run()
    kostenkopf(f'Gefundene Parameter im {name}', st)
