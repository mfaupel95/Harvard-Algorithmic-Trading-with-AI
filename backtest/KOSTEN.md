# Kostenmodell der Beispiel-Backtests

Ein Backtest ohne Kostenmodell ist keine Aussage. Beide Beispielskripte tragen deshalb
einen festen Kostensatz mit, und jedes Ergebnis wird mit `Kosten je Runde`,
`Anzahl Runden` und `netto je Runde` ausgewiesen (`kostenkopf()`).

## Der Kostensatz

| Größe | Wert | wo |
| --- | --- | --- |
| Kommission je Seite | `0.002` (0,2 %) | `KOMMISSION_JE_SEITE` |
| Spread je Seite | `0.0005` (5 Basispunkte) | `SPREAD` |
| Kapital | `100000` | `KAPITAL` |
| Kosten je Runde (Kauf + Verkauf) | **0,5 %** | `(0.002 + 0.0005) * 2` |

`backtesting` 0.6.6 nennt den Spread-Parameter `spread` — es gibt dort kein
`slippage=`. Setzt man `spread` nicht, rechnet der Backtest mit null Spreadkosten.

## Datenbasis

`backtest/data/BTC-6h-1000wks-data.csv`: **12.903 Kerzen**, 2015-07-20 bis 2024-05-19,
Kapital 100.000, Kostensatz 0,5 % je Runde.

| Strategie | Parameter | Return | Runden | netto je Runde | Max. Drawdown |
| --- | --- | --- | --- | --- | --- |
| `BBSqueezeADX` | Standard | **−29,98 %** | 217 | −0,138 % | −48,46 % |
| `BBSqueezeADX` | bester Optimierer-Fund | −6,34 % | 379 | −0,017 % | −25,34 % |
| `BollingerBandBreakoutShort` | Standard | **−47,87 %** | 138 | −0,347 % | −51,14 % |
| `BollingerBandBreakoutShort` | bester Optimierer-Fund | −28,87 % | 60 | −0,481 % | −47,27 % |

Allein die Kommissionen des `BBSqueezeADX`-Standardlaufs betragen **72.217 USD** —
72 % des Einsatzes. Das ist der Grund, warum der Kostensatz hier die Aussage ist und
nicht die Rundung.

## Warum die Kommission 0,002 der Repo-Wert ist

`BBSqueezeADX` mit Spread 0, Kommission je Seite variiert (217 Runden, sonst Standard):

| Kommission je Seite | Return | netto je Runde | Max. Drawdown |
| --- | --- | --- | --- |
| 0,0000 | +82,22 % | +0,379 % | −30,12 % |
| 0,0002 | +74,58 % | +0,344 % | −30,11 % |
| 0,0010 | +19,20 % | +0,088 % | −35,19 % |
| 0,0016 | +0,68 % | +0,003 % | — |
| 0,0018 | −4,41 % | −0,020 % | — |
| **0,0020 (Repo-Wert)** | **−18,68 %** | **−0,086 %** | −40,97 % |
| 0,0040 | −52,77 % | −0,259 % | −60,70 % |

**Break-even liegt bei ~0,0016 Kommission je Seite, also 0,32 % je Runde.** Der im
Repo hinterlegte Wert `0.002` liegt über dem Break-even und kehrt das Vorzeichen um:
die Strategie ist bei 0,001 Gebuehr leicht positiv, bei 0,002 negativ. Die
Kostenannahme ist hier nicht die Rundung — sie ist die Aussage.

Mit Spread 0,0005 (der Wert, den die Skripte jetzt setzen) wird es schlimmer:
0,0020 + 0,0005 → −29,98 %.

## Was der Optimierer nicht darstellen kann

`bt.optimize(maximize='Equity Final [$]')` sucht das Maximum ueber das ganze Gitter.

- `bb_squeeze_adx.py` sucht **160** Kombinationen. 40 Zufallskombinationen daraus:
  Mittel **−52,44 %**, sigma **15,67 %**, Minimum −76,67 %, Maximum −24,62 %,
  **0 von 40 positiv** nach Kosten. Median 377 Runden.
  Der Optimierer liefert als besten Fund **−6,34 %** — das liegt 2,9 sigma ueber dem
  Mittel der Stichprobe, genau das Bild eines Maximums aus 160 Ziehungen.
  Dieselbe Kombination geteilt: **+2,29 %** im Suchfenster, **−6,37 %** im
  Prueffenster.
- `template.py` sucht **1440** Kombinationen. Sein bester Fund: **+175,36 %** im
  Suchfenster, **−28,87 %** im Prueffenster (72 bzw. 60 Runden).
- Die Korrelation des Returns zwischen erster und zweiter Fensterhaelfte betraegt ueber
  40 Kombinationen **+0,173** — bei n=40 ist das nicht von null zu unterscheiden
  (5-%-Grenze liegt bei ~0,31). Ein schwacher, nicht signifikanter Zusammenhang ist
  keine tragfaehige Basis fuer einen Parameter.

Deshalb rechnen die Skripte Suchfenster und Prueffenster getrennt aus und setzen die
gefundene Kombination zusaetzlich auf dem Prueffenster. Die Zahl der durchsuchten
Kombinationen wird mit ausgegeben.
