# EmoIter selected display aggregates

This package contains eight selected manuscript figure/table objects and 320 full-precision scalar cells. It supports integrity and frozen-value inspection. It does not contain curated comments, issue/sprint analysis rows, labels, model weights, or a path from those inputs to the reported estimates.

Run `python3 -I code/verify_display.py .` from this directory. Python 3.9 or newer and the standard library suffice; this check has no network or API requirement. Expected: 9 files, 8 objects, 320 cells, `file_hashes_verified: true`. The command checks the frozen payload and manifest; it does not recompute the study.

The data file uses proportion-scale values for V1: multiply by 100 to get the plotted percentage-point differences. See `data/field_schema.json` and `PAPER_OBJECT_MAP.json` for the remaining fields, labels and units. Intervals are working or pointwise uncertainty summaries as described in the manuscript; they are not independent arm tests.

Data and documentation listed in `LICENSES/DATA-CC-BY-4.0.md` use CC BY 4.0; `code/verify_display.py` uses MIT as stated in `LICENSES/CODE-MIT.txt`. The licenses do not cover upstream TAWOS records, messages, model assets, or outside services.
