# In a Colab cell, download the source data if it is not already present.
import subprocess

subprocess.run(
    [
        "wget",
        "-O",
        "/content/raw_data.csv",
        "https://data.ny.gov/api/views/jshw-gkgu/rows.csv?accessType=DOWNLOAD",
    ],
    check=True,
)

import pandas as pd

# Preview a few rows without loading the entire dataset into memory.
df_preview = pd.read_csv("/content/raw_data.csv", nrows=5)
display(df_preview)
df_preview.info()

# Optional Colab display formatting.
from google.colab import data_table

data_table.enable_dataframe_formatter()
data_table.DataTable(df_preview, max_columns=60)

# Inspect the accident date range.
df_dates = pd.read_csv("/content/raw_data.csv", usecols=["Accident Date"])
print(f"Minimum Date: {df_dates['Accident Date'].min()}")
print(f"Maximum Date: {df_dates['Accident Date'].max()}")

# Zip-code summary. Load all columns required for the metrics below.
import numpy as np

zip_cols = [
    "Zip Code",
    "Attorney/Representative",
    "Controverted Date",
    "C-2 Date",
    "First Hearing Date",
    "Claim Identifier",
    "Average Weekly Wage (AWW)",
    "Age at Injury",
    "Hearing Count",
    "Industry Code Description",
]
df = pd.read_csv("/content/raw_data.csv", usecols=zip_cols)
df["is_represented"] = (
    df["Attorney/Representative"].astype(str).str.strip().str.upper() == "Y"
)
df["is_controverted"] = (
    df["Controverted Date"].notna()
    & ~df["Controverted Date"]
    .astype(str)
    .str.strip()
    .str.upper()
    .isin(["NAN", "NONE", "NAT", ""])
)
df["c2_dt"] = pd.to_datetime(df["C-2 Date"], errors="coerce")
df["first_hearing_dt"] = pd.to_datetime(df["First Hearing Date"], errors="coerce")
df["days_c2_to_first_hearing"] = (
    df["first_hearing_dt"] - df["c2_dt"]
).dt.total_seconds() / (24 * 3600)
df.loc[df["days_c2_to_first_hearing"] < 0, "days_c2_to_first_hearing"] = np.nan


def get_top_industry(series):
    cleaned = series.dropna()
    return cleaned.mode().iloc[0] if not cleaned.empty else "Unknown"


zip_summary = (
    df.groupby("Zip Code")
    .agg(
        total_claims=("Claim Identifier", "count"),
        avg_wage=("Average Weekly Wage (AWW)", "mean"),
        avg_age=("Age at Injury", "mean"),
        pct_represented=("is_represented", lambda x: x.mean() * 100),
        pct_controverted=("is_controverted", lambda x: x.mean() * 100),
        avg_hearings=("Hearing Count", "mean"),
        avg_days_c2_to_hearing=("days_c2_to_first_hearing", "mean"),
        top_industry=("Industry Code Description", get_top_industry),
    )
    .reset_index()
)
zip_summary = zip_summary[zip_summary["total_claims"] >= 100].sort_values(
    by="total_claims", ascending=False
)
display(zip_summary.head(15))

# Statewide body-part and injury summaries.
body_cols = ["WCIO Part Of Body Description", "OIICS Nature of Injury Description"]
df = pd.read_csv("/content/raw_data.csv", usecols=body_cols)
top_body_parts_statewide = (
    df.dropna(subset=["WCIO Part Of Body Description"])
    .groupby("WCIO Part Of Body Description", as_index=False)
    .size()
    .rename(
        columns={
            "WCIO Part Of Body Description": "body_part",
            "size": "claim_count",
        }
    )
    .sort_values(by="claim_count", ascending=False)
    .reset_index(drop=True)
)
top_body_parts_statewide["pct_of_total"] = (
    top_body_parts_statewide["claim_count"]
    / top_body_parts_statewide["claim_count"].sum()
    * 100
)
print("--- Top 10 Body Parts Statewide (WCIO) ---")
display(top_body_parts_statewide.head(10))

top_injuries_statewide = (
    df.dropna(subset=["OIICS Nature of Injury Description"])
    .groupby("OIICS Nature of Injury Description", as_index=False)
    .size()
    .rename(
        columns={
            "OIICS Nature of Injury Description": "Injury Type",
            "size": "claim_count",
        }
    )
    .sort_values(by="claim_count", ascending=False)
    .reset_index(drop=True)
)
top_injuries_statewide["pct_of_total"] = (
    top_injuries_statewide["claim_count"]
    / top_injuries_statewide["claim_count"].sum()
    * 100
)
print("--- Top 10 Injuries Statewide (OIICS) ---")
display(top_injuries_statewide.head(10))

# Year-over-year outcomes and controversion trends.
import matplotlib.pyplot as plt

df = pd.read_csv("/content/raw_data.csv")
df["accident_year"] = pd.to_numeric(
    df["Accident Date"].astype(str).str[-4:], errors="coerce"
)
df["is_controverted"] = (
    df["Controverted Date"].notna()
    & ~df["Controverted Date"]
    .astype(str)
    .str.strip()
    .str.upper()
    .isin(["NAN", "NONE", "NAT", ""])
)
injury_type = df["Claim Injury Type"].astype(str).str.strip().str.upper()
no_benefit_types = ["NON-COMP", "CANCELLED"]
benefit_types = ["TEMPORARY", "PPD SCH LOSS", "PPD NSL", "PTD", "DEATH"]
df["outcome_category"] = np.select(
    [
        injury_type.str.contains("|".join(no_benefit_types), na=False),
        injury_type.str.contains("MED ONLY", na=False),
        injury_type.str.contains("|".join(benefit_types), na=False),
    ],
    ["No Benefit (Disallowed/Cancelled)", "Medical Only", "Cash Benefit"],
    default="Other/Pending",
)
df["has_cash_benefit"] = df["outcome_category"] == "Cash Benefit"
df["has_no_benefit"] = df["outcome_category"] == "No Benefit (Disallowed/Cancelled)"
yoy_trends = (
    df.dropna(subset=["accident_year"])
    .query("2000 <= accident_year <= 2026")
    .groupby("accident_year")
    .agg(
        total_claims=("Claim Identifier", "count"),
        pct_controverted=("is_controverted", lambda x: x.mean() * 100),
        pct_benefit=("has_cash_benefit", lambda x: x.mean() * 100),
        pct_no_benefit=("has_no_benefit", lambda x: x.mean() * 100),
        pct_medical_only=("outcome_category", lambda x: (x == "Medical Only").mean() * 100),
    )
    .reset_index()
    .sort_values(by="accident_year")
)
display(yoy_trends.tail(15))

plt.figure(figsize=(11, 5))
for column, label, marker, color in [
    ("pct_controverted", "% Controverted", "o", "crimson"),
    ("pct_benefit", "% Cash Benefit Awarded", "s", "steelblue"),
    ("pct_no_benefit", "% No Benefit (Disallowed/Cancelled)", "^", "darkorange"),
    ("pct_medical_only", "% Medical Only", "^", "purple"),
]:
    plt.plot(yoy_trends["accident_year"], yoy_trends[column], label=label, marker=marker, color=color, linewidth=2)
plt.title("NYS Workers' Comp: Outcome & Controversion Trends YoY", fontsize=14, pad=12)
plt.xlabel("Accident Year", fontsize=11)
plt.ylabel("Percentage of Total Claims (%)", fontsize=11)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(frameon=True)
plt.tight_layout()
plt.show()

# Industry claim-share trends.
needed_cols = ["Accident Date", "Industry Code Description"]
df = pd.read_csv("/content/raw_data.csv", usecols=needed_cols)
df["accident_year"] = pd.to_numeric(df["Accident Date"].astype(str).str[-4:], errors="coerce")
df_sub = df.query("2000 <= accident_year <= 2026").copy()
df_sub["industry_clean"] = df_sub["Industry Code Description"].fillna("Unknown").str.strip()
top_industries = (
    df_sub[df_sub["industry_clean"] != "Unknown"]["industry_clean"].value_counts().nlargest(6).index
)
df_sub["industry_grouped"] = df_sub["industry_clean"].where(
    df_sub["industry_clean"].isin(top_industries), "All Other Industries"
)
industry_trends = pd.crosstab(
    df_sub["accident_year"], df_sub["industry_grouped"], normalize="index"
) * 100
plot_cols = [col for col in top_industries if col in industry_trends.columns]
if "All Other Industries" in industry_trends.columns:
    plot_cols.append("All Other Industries")
industry_trends = industry_trends[plot_cols]
plt.figure(figsize=(12, 6))
markers = ["o", "s", "^", "D", "v", "P", "X"]
palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#7f7f7f"]
for idx, col in enumerate(industry_trends.columns):
    is_other = col == "All Other Industries"
    plt.plot(
        industry_trends.index,
        industry_trends[col],
        marker=markers[idx % len(markers)],
        linewidth=2.0 if not is_other else 1.5,
        linestyle="-" if not is_other else "--",
        color=palette[idx % len(palette)],
        label=col,
    )
plt.title("Shift in Claim Volume Share by Industry in New York (2000–2026)", fontsize=13, pad=14, fontweight="bold")
plt.xlabel("Accident Year", fontsize=11, fontweight="bold")
plt.ylabel("Share of Annual Claims (%)", fontsize=11, fontweight="bold")
plt.grid(True, linestyle=":", alpha=0.6)
plt.legend(title="Industry Sector", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True, fontsize=9.5)
plt.tight_layout()
plt.show()

# Median age and share of soft-tissue injuries.
import gc

needed_cols = ["Accident Date", "Age at Injury", "WCIO Nature of Injury Description"]
df = pd.read_csv("/content/raw_data.csv", usecols=needed_cols)
df["accident_year"] = pd.to_numeric(df["Accident Date"].astype(str).str[-4:], errors="coerce")
df["age_clean"] = pd.to_numeric(df["Age at Injury"], errors="coerce")
df_sub = df.query("2000 <= accident_year <= 2026 and 14 <= age_clean <= 85").copy()
del df
gc.collect()
nature_series = df_sub["WCIO Nature of Injury Description"].fillna("").astype(str).str.upper()
df_sub["is_strain"] = nature_series.str.contains("STRAIN|SPRAIN|TEAR", regex=True)
del nature_series
gc.collect()
trends = (
    df_sub.groupby("accident_year")
    .agg(median_age=("age_clean", "median"), pct_strain=("is_strain", lambda x: x.mean() * 100))
    .reset_index()
)
del df_sub
gc.collect()
fig, ax1 = plt.subplots(figsize=(11, 5.5))
line1 = ax1.plot(trends["accident_year"], trends["pct_strain"], color="#7570b3", linewidth=2.5, marker="s", label="% Sprains, Strains & Tears (WCIO)")
ax1.set_xlabel("Accident Year", fontsize=11, fontweight="bold")
ax1.set_ylabel("% of Annual Claims", fontsize=11, fontweight="bold", color="#7570b3")
ax1.tick_params(axis="y", labelcolor="#7570b3")
ax1.grid(True, linestyle=":", alpha=0.6)
ax2 = ax1.twinx()
line2 = ax2.plot(trends["accident_year"], trends["median_age"], color="#1b9e77", linewidth=2.5, marker="^", label="Median Age at Injury")
ax2.set_ylabel("Median Age at Injury (Years)", fontsize=11, fontweight="bold", color="#1b9e77")
ax2.tick_params(axis="y", labelcolor="#1b9e77")
lines = line1 + line2
ax1.legend(lines, [line.get_label() for line in lines], loc="upper left", frameon=True)
plt.title("Workforce Aging vs. Growth in Soft-Tissue / Strain Claims (2000–2026)", fontsize=13, pad=14, fontweight="bold")
plt.tight_layout()
plt.show()

# Representation and judicial process comparison.
cols = ["Attorney/Representative", "Highest Process"]
df = pd.read_csv("/content/raw_data.csv", usecols=cols)
is_represented = df["Attorney/Representative"] == "Y"
went_to_judge = df["Highest Process"].str.startswith("4", na=False)
comparison = went_to_judge.groupby(is_represented).agg(
    total_claims="count", went_to_judge_count="sum", pct_went_to_judge="mean"
).rename(index={False: "Unrepresented (N)", True: "Represented (Y)"})
comparison["pct_went_to_judge"] *= 100
display(comparison.round(2))
rate_unrep = comparison.loc["Unrepresented (N)", "pct_went_to_judge"]
rate_rep = comparison.loc["Represented (Y)", "pct_went_to_judge"]
multiplier = rate_rep / rate_unrep if rate_unrep > 0 else 0
print(f"\nRepresented claims are {multiplier:.2f}x as likely to go before a Judge ({rate_rep:.1f}% vs. {rate_unrep:.1f}%).")

# Inspect claim identifier 111.
df = pd.read_csv("/content/raw_data.csv")
with pd.option_context("display.max_rows", None):
    display(df[df["Claim Identifier"] == 111].T)

# Descriptive association of IME/reporting lag with reaching a judge.
cols = ["Accident Date", "C-2 Date", "IME-4 Count", "Highest Process"]
df = pd.read_csv("/content/raw_data.csv", usecols=cols)
went_to_judge = df["Highest Process"].str.startswith("4", na=False)
accident_dt = pd.to_datetime(df["Accident Date"], errors="coerce")
c2_dt = pd.to_datetime(df["C-2 Date"], errors="coerce")
report_lag = (c2_dt - accident_dt).dt.days
valid_lag_mask = report_lag.between(0, 365)
del accident_dt, c2_dt
gc.collect()
has_ime = pd.to_numeric(df["IME-4 Count"], errors="coerce").fillna(0) > 0
corr_ime = went_to_judge.corr(has_ime.astype(int))
corr_reporting_lag = went_to_judge[valid_lag_mask].corr(report_lag[valid_lag_mask])
print("=== STATISTICAL CORRELATIONS (r) ===")
print(f"Correlation (Having an IME -> Reaching Judge): {corr_ime:.4f}")
print(f"Correlation (Reporting Lag Days -> Reaching Judge): {corr_reporting_lag:.4f}\n")
print("=== ESCALATION RATE BY IME STATUS ===")
ime_summary = went_to_judge.groupby(has_ime).agg(
    total_claims="count", escalated_count="sum", pct_reaching_judge=lambda x: x.mean() * 100
).rename(index={False: "No IME-4", True: "Had IME-4"})
display(ime_summary.round(2))
print("\n=== ESCALATION RATE BY REPORTING SPEED TIER ===")
lag_buckets = pd.cut(
    report_lag[valid_lag_mask],
    bins=[-1, 2, 7, 14, 30, 365],
    labels=["0-2 Days", "3-7 Days", "8-14 Days", "15-30 Days", "30+ Days"],
)
lag_summary = went_to_judge[valid_lag_mask].groupby(lag_buckets).agg(
    total_claims="count", escalated_count="sum", pct_reaching_judge=lambda x: x.mean() * 100
)
display(lag_summary.round(2))
del df, went_to_judge, report_lag, has_ime
gc.collect()
