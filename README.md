# Time Series Analysis & Forecasting

A three-day practical course built on [*Forecasting: Principles and Practice, the Pythonic Way*](https://otexts.com/fpppy/) (Hyndman et al.), using the `statsforecast` / `utilsforecast` stack.

---

## 🚀 Labs & Google Colab Links

You can run the labs directly in Google Colab with one click:

| Section | Notebook | Colab Direct Link | Solutions |
| :--- | :--- | :--- | :--- |
| **Pre-work** | `labs/00_pre_work.ipynb` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NaifMersal/time-series-analysis-and-forecasting/blob/main/labs/00_pre_work.ipynb) | [Solution](https://colab.research.google.com/github/NaifMersal/time-series-analysis-and-forecasting/blob/main/labs/solutions/00_pre_work.ipynb) |
| **Day 1: Structure & Diagnostics** | `labs/01_day1_structure_and_diagnostics.ipynb` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NaifMersal/time-series-analysis-and-forecasting/blob/main/labs/01_day1_structure_and_diagnostics.ipynb) | [Solution](https://colab.research.google.com/github/NaifMersal/time-series-analysis-and-forecasting/blob/main/labs/solutions/01_day1_structure_and_diagnostics.ipynb) |
| **Day 2: Toolbox & Evaluation** | `labs/02_day2_toolbox_and_evaluation.ipynb` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NaifMersal/time-series-analysis-and-forecasting/blob/main/labs/02_day2_toolbox_and_evaluation.ipynb) | [Solution](https://colab.research.google.com/github/NaifMersal/time-series-analysis-and-forecasting/blob/main/labs/solutions/02_day2_toolbox_and_evaluation.ipynb) |

---

## 🛠 Local Setup

If you prefer to run locally:

```bash
# Clone the repository
git clone https://github.com/NaifMersal/time-series-analysis-and-forecasting.git
cd time-series-analysis-and-forecasting

# Install dependencies using uv
uv sync --extra dev

# Verify your environment
python scripts/check_env.py
```
