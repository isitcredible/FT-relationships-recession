# FT relationship recession — replication data and code

Replication package for the audit of John Burn-Murdoch,
"The relationship recession is going global," *Financial Times*,
11 January 2025.

For the full write-up, see
[isitcredible.com/cases](https://isitcredible.com/cases) (forthcoming).

## Contents

```
data/
  ft_chart*.csv                  FT chart data extracted from Flourish embeds
  tfr_annual.csv                 UN WPP 2024 TFR (from 10_download_tfr.py)
  fertility_panel.csv            CDC/NCHS panel for Stone decomposition
  eurostat_coupling_western.csv  Eurostat legal-marital-status proxy

scripts/
  _style.py                      Shared FT-inspired matplotlib style
  _stone.py, _audit.py, _eurostat.py
  01_extract_flourish_data.py    Parse saved embed HTML (needs archive/)
  02_download_acs.py               Build fertility panel from CDC/NCHS
  03_stone_decomposition.py        Chart 1 Stone counterfactual
  04_audit_chart01.py
  06_ilo_coupling_extract.py       Eurostat Western coupling pull
  08_harmonize_global_coupling.py
  09_audit_chart03.py
  10_download_tfr.py
  11_coupling_tfr_index.py         Chart 5 index rebuild
  12_audit_chart05.py
  14_gsma_verify.py                Chart 4 GSMA table verify

figures/
  chart01_stone_decomposition.png
```

## Reproducing

From the case-study root (parent of `repo/`), with saved FT page in `archive/`:

```bash
pip install -r repo/requirements.txt
python scripts/01_extract_flourish_data.py
python scripts/02_download_acs.py
python scripts/03_stone_decomposition.py
python scripts/04_audit_chart01.py
python scripts/06_ilo_coupling_extract.py   # ~7 min (Eurostat API)
python scripts/08_harmonize_global_coupling.py
python scripts/09_audit_chart03.py
python scripts/10_download_tfr.py
python scripts/11_coupling_tfr_index.py
python scripts/12_audit_chart05.py
python scripts/14_gsma_verify.py
```

Audit CSVs land in `output/`. See `findings.md` in the parent folder for verdicts.

## Sources

- US TFR decomposition: CDC NCHS unmarried birth rates; NVSR Table 10; Census CPS marital shares; Lyman Stone methodology
- Global coupling: Eurostat `demo_pjanmarsta` (Western proxy); FT embed for full panel
- TFR index: UN World Population Prospects 2024
- GSMA Mobile Gender Gap Report 2018, Table 2

## Licence

MIT. Author: Joseph Francis.

Part of [isitcredible.com](https://isitcredible.com), run by The Catalogue of Errors Ltd.
