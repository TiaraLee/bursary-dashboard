import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re

# Load the updated cleaned dataset and qualification key table
df = pd.read_csv("cleaned_bursary_data_updated.csv")
qual_key = pd.read_csv("qualification_key_table_updated.csv")

# Normalize qualification names to remove year references (e.g., "(1st Year)", "(3rd Year)")
df["Qualification"] = df["Qualification"].apply(lambda x: re.sub(r"\s*\(\d+(st|nd|rd|th) Year\)", "", x).strip())
qual_key["Qualification"] = qual_key["Qualification"].apply(lambda x: re.sub(r"\s*\(\d+(st|nd|rd|th) Year\)", "", x).strip())

# Remove duplicates from qualification key based on Institution and normalized Qualification
qual_key = qual_key.drop_duplicates(subset=["Institution", "Qualification"])

# Combine "Black/African" and "Black" into a single category
df["Ethnic Group"] = df["Ethnic Group"].replace({"Black/African": "Black"})

st.set_page_config(layout="wide")
st.title("2024/2025 Bursary Spend Dashboard")

# --- Row 1: Institution and Ethnic Group Pie Charts ---
st.markdown("### Distribution by Institution and Ethnic Group")
col1, col2 = st.columns(2)

with col1:
    institution_funds = df.groupby("Institution")["Total Funds"].sum()
    fig1, ax1 = plt.subplots(figsize=(2.5, 2.5))
    ax1.pie(institution_funds, labels=institution_funds.index, autopct="%1.2f%%", startangle=140)
    ax1.axis("equal")
    st.pyplot(fig1)
    st.caption("Total Funds by Institution")

with col2:
    ethnic_funds = df.groupby("Ethnic Group")["Total Funds"].sum()
    fig3, ax3 = plt.subplots(figsize=(2.5, 2.5))
    ax3.pie(ethnic_funds, labels=ethnic_funds.index, autopct="%1.2f%%", startangle=140)
    ax3.axis("equal")
    st.pyplot(fig3)
    st.caption("Total Funds by Ethnic Group")

# --- Row 2: Bar Chart - Total Funds by Qualification ---
st.markdown("### Total Funds by Qualification")
qualification_funds = df.groupby("Qualification")["Total Funds"].sum().sort_values(ascending=False)
col_q1, _ = st.columns([3, 1])
with col_q1:
    fig2, ax2 = plt.subplots(figsize=(6, 2.5))
    qualification_funds.plot(kind='barh', ax=ax2, color='skyblue', width=0.95)
    ax2.set_xlabel("Total Funds per Category")
    ax2.invert_yaxis()
    st.pyplot(fig2)

# --- Row 3: Bar Chart - Qualification and Gender ---
st.markdown("### Total Funds by Qualification and Gender")
qualification_gender_funds = df.groupby(["Qualification", "Gender"])["Total Funds"].sum().reset_index()
qualification_gender_pivot = qualification_gender_funds.groupby(["Qualification", "Gender"]).sum().unstack().fillna(0)
col_q2, _ = st.columns([3, 1])
with col_q2:
    fig4, ax4 = plt.subplots(figsize=(6, 2.5))
    qualification_gender_pivot.plot(kind='bar', ax=ax4, width=0.85)
    ax4.set_ylabel("Sum of Total Funds")
    ax4.set_ylim(0, 5000000)
    ax4.set_xlabel("Qualification")
    st.pyplot(fig4)

# --- Row 4: Donut Charts - Ethnic Group by Gender ---
st.markdown("### Ethnic Group Breakdown by Gender (Cleaned View)")
ethnic_gender_funds = df.groupby(["Gender", "Ethnic Group"])["Total Funds"].sum().reset_index()
ethnic_gender_funds["Ethnic Group"] = ethnic_gender_funds["Ethnic Group"].replace({"Black/African": "Black"})

# Normalize ethnic groups
genders = ["Female", "Male"]
all_groups = ["Black", "Coloured", "Indian", "White"]

grid = pd.MultiIndex.from_product([genders, all_groups], names=["Gender", "Ethnic Group"])
ethnic_gender_funds = ethnic_gender_funds.set_index(["Gender", "Ethnic Group"]).reindex(grid, fill_value=0).reset_index()

cols = st.columns(2)
colors = {
    "Black": "#1f77b4",
    "Coloured": "#ff7f0e",
    "Indian": "#2ca02c",
    "White": "#d62728",
    "Other": "#9467bd"
}

for i, gender in enumerate(genders):
    data = ethnic_gender_funds[ethnic_gender_funds["Gender"] == gender].set_index("Ethnic Group")["Total Funds"]
    data = data.sort_values(ascending=False)
    total = data.sum()

    # Combine small slices (less than 5%) into "Other"
    small_slices = data / total < 0.05
    if small_slices.sum() > 0:
        other_total = data[small_slices].sum()
        data = data[~small_slices]
        if other_total > 0:
            data["Other"] = other_total

    # Create labels with percentage and value
    labels = []
    for ethnic, val in data.items():
        percentage = val/total
        if percentage < 0.001:
            label = f"{ethnic} (0.0%)"
        else:
            label = f"{ethnic} ({percentage:.1%})"
        labels.append(label)

    values = data.values

    fig, ax = plt.subplots(figsize=(4, 4))
    
    # Create donut chart
    wedges, texts = ax.pie(
        values,
        labels=labels if len(data) <= 4 else None,
        colors=[colors.get(label, "#cccccc") for label in data.index],
        startangle=90,
        wedgeprops={'linewidth': 1, 'edgecolor': 'white', 'width': 0.6},  # Width controls donut thickness
        textprops={'fontsize': 9}
    )
    
    # Add center circle to make it a donut
    centre_circle = plt.Circle((0,0), 0.3, color='white', fc='white', linewidth=0)
    ax.add_artist(centre_circle)
    
    # Add total in the center
    ax.text(0, 0, f"Total\nR{total:,.0f}", ha='center', va='center', fontsize=10)
    
    # Add legend if needed
    if len(data) > 4:
        ax.legend(
            wedges,
            [f"{l}\nR{int(v):,}" for l, v in zip(labels, values)],
            title="Ethnic Groups",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=8
        )
    else:
        # Adjust label positions
        for text in texts:
            text.set_horizontalalignment('center')
            text.set_fontsize(9)
    
    ax.set_title(gender, fontsize=14)
    ax.axis("equal")
    plt.tight_layout()
    cols[i].pyplot(fig)

# --- Note for grouped "Other" slices ---
other_notes = []

for gender in genders:
    gender_data = ethnic_gender_funds[
        ethnic_gender_funds["Gender"] == gender
    ].set_index("Ethnic Group")["Total Funds"]
    gender_total = gender_data.sum()
    
    small = gender_data[gender_data / gender_total < 0.05]
    small = small[small > 0]  # Only include actual values

    if not small.empty:
        breakdown = ", ".join([f"{ethnic} (R{amount:,.0f})" for ethnic, amount in small.items()])
        note = f"**{gender} – 'Other' includes:** {breakdown}"
        other_notes.append(note)

if other_notes:
    st.markdown("##### Note on 'Other' Category")
    for note in other_notes:
        st.markdown(note)

# --- Row 5: Qualification Key Table ---
st.markdown("### Qualification Key Table")
with st.expander("View Qualification Key Table"):
    st.dataframe(qual_key, use_container_width=True)

