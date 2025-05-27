import pandas as pd
import streamlit as st
import plotly.express as px
import pydeck as pdk

st.set_page_config(layout="wide", page_title="Rig Comparison Dashboard", page_icon="📊")

# Custom Styling
st.markdown("""
<style>
body { background-color: #f5f7fa; }
h1 { font-size: 2.4rem; font-weight: 700; color: #004578; }
[data-testid="stMetric"] {
  background-color: #ffffff;
  border: 1px solid #d0d6dd;
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  text-align: center;
}
.stButton button {
  background-color: #0078d4;
  color: white;
  font-weight: bold;
  border-radius: 8px;
  padding: 0.4rem 1rem;
  border: none;
  margin-top: 1.6rem;
}
.stButton button:hover {
  background-color: #005ea2;
}
.css-1cpxqw2, .css-1y4p8pa {
  background-color: #ffffff !important;
  border: 1px solid #d0d6dd !important;
  border-radius: 10px !important;
  padding: 0.3rem !important;
}
.stTabs [data-baseweb="tab"] {
  font-size: 1rem;
  padding: 10px;
  border-radius: 8px 8px 0 0;
  background-color: #eaf1fb;
  color: #004578;
  margin-right: 0.5rem;
}
.stTabs [aria-selected="true"] {
  background-color: #0078d4 !important;
  color: white !important;
  font-weight: bold;
}
.stDataFrame {
  border-radius: 12px;
  border: 1px solid #d0d6dd;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# Upload Section
with st.expander("📁 Upload your CSV file", expanded=True):
    uploaded_file = st.file_uploader("", type="csv")
    if uploaded_file:
        data = pd.read_csv(uploaded_file, quotechar='"', skipinitialspace=True, engine="python")
        st.success("CSV uploaded and loaded successfully!")



    else:
        st.warning("Please upload a CSV file to get started.")
        st.stop()

# Filters
st.title("📊 Rig Comparison Dashboard")

with st.container():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_operator = st.selectbox("Select Operator", ["All"] + sorted(data["Operator"].dropna().unique().tolist()))
    with col2:
        filtered_by_op = data if selected_operator == "All" else data[data["Operator"] == selected_operator]
        selected_contractor = st.selectbox("Select Contractor", ["All"] + sorted(filtered_by_op["Contractor"].dropna().unique().tolist()))
    with col3:
        filtered_by_contractor = filtered_by_op if selected_contractor == "All" else filtered_by_op[filtered_by_op["Contractor"] == selected_contractor]
        selected_shaker = st.selectbox("Select Shaker", ["All"] + sorted(filtered_by_contractor["flowline_Shakers"].dropna().unique().tolist()))
    with col4:
        filtered_by_shaker = filtered_by_contractor if selected_shaker == "All" else filtered_by_contractor[filtered_by_contractor["flowline_Shakers"] == selected_shaker]
        selected_hole = st.selectbox("Select Hole Size", ["All"] + sorted(filtered_by_shaker["Hole_Size"].dropna().unique().tolist()))

    filtered = filtered_by_shaker if selected_hole == "All" else filtered_by_shaker[filtered_by_shaker["Hole_Size"] == selected_hole]

# ---------- METRICS ----------
st.markdown("### 📈 Key Performance Metrics")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Avg Total Dilution", f"{filtered['Total_Dil'].mean():,.2f} BBLs")
with m2:
    st.metric("Avg SCE", f"{filtered['Total_SCE'].mean():,.2f}")
with m3:
    st.metric("Avg DSRE", f"{filtered['DSRE'].mean()*100:.1f}%")

# ---------- MAIN TABS ----------
tabs = st.tabs(["🧾 Well Overview", "📋 Summary & Charts", "📊 Statistical Insights", "📈 Advanced Analytics", "🧮 Multi-Well Comparison"])



# ---------- TAB 1: WELL OVERVIEW ----------
with tabs[0]:
    st.markdown("### 🧾 Well Overview")
    st.markdown("Analyze well-level performance metrics as grouped column bar charts.")

    st.markdown("### 🧾 Well-Level Overview")

    numeric_cols = [
        "DSRE", "SCE_Loss_Ratio", "Total_SCE", "Total_Dil", "ROP", "Temp", "DOW", "AMW",
        "Drilling_Hours", "Haul_OFF", "Base_Oil", "Water", "Weight_Material",
        "Chemicals", "Dilution_Ratio", "Solids_Generated"
    ]

    available_cols = [col for col in numeric_cols if col in filtered.columns]
    melted_df = filtered[["Well_Name"] + available_cols].melt(id_vars="Well_Name", var_name="Metric", value_name="Value")

    if not melted_df.empty:
        fig = px.bar(melted_df, x="Well_Name", y="Value", color="Metric", barmode="group",
                     title="Well Name vs Key Metrics", height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid numeric data found for chart.")


# ---------- TAB 2: SUMMARY + CHARTS ----------
with tabs[1]:
    chart1, chart2 = st.columns(2)

    with chart1:
        st.markdown("### 📌 Depth vs DOW")
        subset = filtered.dropna(subset=["Well_Name"])
        y_cols = [col for col in ["Depth", "DOW"] if col in subset.columns]
        if y_cols:
            fig1 = px.bar(subset, x="Well_Name", y=y_cols, barmode='group', height=400,
                          labels={"value": "Barrels", "variable": "Metric"},
                          color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig1, use_container_width=True)

    with chart2:
        st.markdown("### 🌈 Dilution Breakdown")
        y_cols = [col for col in ["Base_Oil", "Water", "Weight_Material", "Chemicals"] if col in subset.columns]
        if y_cols:
            fig2 = px.bar(subset, x="Well_Name", y=y_cols, barmode="stack", height=400,
                          color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 📈 DSRE vs Ratios")
    if "DSRE" in subset.columns:
        try:
            fig3 = px.bar(subset, x="Well_Name", y="DSRE", height=400,
                          labels={"DSRE": "DSRE"}, color_discrete_sequence=["#66c2a5"])
            if "SCE_Loss_Ratio" in subset.columns:
                fig3.add_scatter(x=subset["Well_Name"], y=subset["SCE_Loss_Ratio"], mode='lines+markers', name="SCE Loss Ratio",
                                 line=dict(color="red"))
            if "Dilution_Ratio" in subset.columns:
                fig3.add_scatter(x=subset["Well_Name"], y=subset["Dilution_Ratio"], mode='lines+markers', name="Dilution Ratio",
                                 line=dict(color="gray"))
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.error(f"Chart rendering error: {e}")


    st.markdown("### 📊 Additional Ratios Comparison")
    ratio_cols = [col for col in ["Dilution_Ratio", "SCE_Loss_Ratio"] if col in subset.columns]
    if ratio_cols:
        try:
            fig4 = px.line(subset, x="Well_Name", y=ratio_cols, markers=True,
                           labels={"value": "Ratio", "variable": "Metric"},
                           title="Dilution vs SCE Loss Ratios")
            st.plotly_chart(fig4, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering ratio comparison chart: {e}")
    else:
        st.info("Dilution_Ratio and SCE_Loss_Ratio columns not found for ratio comparison.")


# ---------- TAB 3: STATISTICS & INSIGHTS ----------
with tabs[2]:
    st.markdown("### 📊 Statistical Summary & Insights")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Mean DSRE", f"{filtered['DSRE'].mean()*100:.2f}%")
    k2.metric("Max Haul Off", f"{filtered['Haul_OFF'].max():,.0f}")
    k3.metric("Avg SCE", f"{filtered['Total_SCE'].mean():,.2f}")
    k4.metric("Avg Dilution", f"{filtered['Total_Dil'].mean():,.2f}")

    st.markdown("#### 🔍 Automatic Insights")
    if 'DSRE' in filtered.columns:
        high_eff = filtered[filtered['DSRE'] > 0.9]
        low_eff = filtered[filtered['DSRE'] < 0.6]
        st.markdown(f"✅ **High Efficiency Wells (DSRE > 90%)**: {len(high_eff)}")
        st.markdown(f"⚠️ **Low Efficiency Wells (DSRE < 60%)**: {len(low_eff)}")
    else:
        st.info("DSRE column not found for efficiency insights.")

    st.markdown("---")
    st.markdown("You can extend this section with clustering, correlation matrix, or predictive modeling based on data quality.")

# ---------- TAB 4: ADVANCED ANALYTICS ----------
with tabs[3]:
    st.markdown("### 🤖 Advanced Analytics & Trends")

    st.markdown("#### 📌 ROP vs Temperature")
    if "ROP" in filtered.columns and "Temp" in filtered.columns:
        try:
            fig_rop_temp = px.scatter(
                filtered, x="ROP", y="Temp", color="Well_Name",
                title="ROP vs Temperature",
                labels={"ROP": "Rate of Penetration", "Temp": "Temperature (°F)"}
            )
            st.plotly_chart(fig_rop_temp, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering ROP vs Temp chart: {e}")

    st.markdown("#### 📌 Base Oil vs Water Composition")
    if "Base_Oil" in filtered.columns and "Water" in filtered.columns:
        try:
            fig_bo_water = px.scatter(
                filtered, x="Base_Oil", y="Water", size="Total_Dil",
                color="Well_Name", title="Base Oil vs Water Breakdown",
                labels={"Base_Oil": "Base Oil (bbl)", "Water": "Water (bbl)"}
            )
            st.plotly_chart(fig_bo_water, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering Base Oil vs Water chart: {e}")

    st.markdown("#### 📌 Correlation Heatmap")
    try:
        corr_cols = ["DSRE", "Total_SCE", "Total_Dil", "SCE_Loss_Ratio", "Dilution_Ratio", "ROP", "AMW", "Haul_OFF"]
        corr_data = filtered[corr_cols].dropna()
        corr_matrix = corr_data.corr()
        fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale='Blues')
        st.plotly_chart(fig_corr, use_container_width=True)
    except Exception as e:
        st.error(f"Correlation heatmap error: {e}")


# ---------- TAB 5: MULTI-WELL COMPARISON ----------
with tabs[4]:
    st.markdown("### 🧮 Derrick vs Non-Derrick Comparison")

    compare_cols = [
        "DSRE", "SCE_Loss_Ratio", "Total_SCE", "Total_Dil", "ROP", "Temp", "DOW", "AMW",
        "Drilling_Hours", "Haul_OFF", "Base_Oil", "Water", "Weight_Material",
        "Chemicals", "Dilution_Ratio", "Solids_Generated"
    ]

    if "flowline_Shakers" in filtered.columns:
        filtered["Shaker_Type"] = filtered["flowline_Shakers"].apply(
            lambda x: "Derrick" if isinstance(x, str) and "derrick" in x.lower() else "Non-Derrick"
        )

        selected_metrics = st.multiselect("Select Metrics to Compare", compare_cols, default=["DSRE", "ROP", "Total_Dil"])

        if selected_metrics:
            try:
                available = ["Well_Name", "Shaker_Type"] + [col for col in selected_metrics if col in filtered.columns]
                melted_df = filtered[available].melt(
                    id_vars=["Well_Name", "Shaker_Type"], var_name="Metric", value_name="Value"
                )
                fig = px.bar(
                    melted_df, x="Well_Name", y="Value", color="Shaker_Type", facet_col="Metric",
                    title="Derrick vs Non-Derrick Comparison by Well and Metric", height=600,
                    color_discrete_map={"Derrick": "#007635", "Non-Derrick": "lightgrey"}
                )
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("### 📋 Group Summary Statistics")
                summary_metrics = [col for col in ["DSRE", "ROP", "Total_SCE", "Total_Dil", "Dilution_Ratio", "SCE_Loss_Ratio"] if col in filtered.columns]
                if summary_metrics:
                    kpi_df = filtered.groupby("Shaker_Type")[summary_metrics].mean().round(2).reset_index()

                    for _, row in kpi_df.iterrows():
                        color = "#007635" if row["Shaker_Type"] == "Derrick" else "#d3d3d3"
                        st.markdown(f'''
                            <div style="background-color:{color};padding:1rem;border-radius:10px;margin-bottom:1rem;">
                                <h4 style="color:white;">{row['Shaker_Type']} Shakers</h4>
                                <div style="display:flex;justify-content:space-between;color:white;">
                                    <div>Avg DSRE: <b>{row.get("DSRE", 0) * 100:.1f}%</b></div>
                                    <div>Avg ROP: <b>{row.get("ROP", "N/A")}</b></div>
                                    <div>Total Dilution: <b>{row.get("Total_Dil", "N/A")}</b></div>
                                    <div>SCE: <b>{row.get("Total_SCE", "N/A")}</b></div>
                                    <div>Dilution Ratio: <b>{row.get("Dilution_Ratio", "N/A")}</b></div>
                                    <div>SCE Loss Ratio: <b>{row.get("SCE_Loss_Ratio", "N/A")}</b></div>
                                </div>
                            </div>
                        ''', unsafe_allow_html=True)

                st.markdown("### 🏆 Ratio-Based Scoring & Rankings")
                scoring_df = filtered.copy()
                if "DSRE" in scoring_df.columns:
                    scoring_df["Efficiency Score"] = (
                        scoring_df["DSRE"].fillna(0) * 100
                        - pd.Series(scoring_df.get("Dilution_Ratio", 0)).fillna(0) * 10
                        - pd.Series(scoring_df.get("SCE_Loss_Ratio", 0)).fillna(0) * 10
                    )
                    rank_df = scoring_df[["Well_Name", "Shaker_Type", "Efficiency Score"]].sort_values(by="Efficiency Score", ascending=False).reset_index(drop=True)
                    st.dataframe(rank_df, use_container_width=True)
                else:
                    st.warning("DSRE column missing for scoring.")
            except Exception as e:
                st.error(f"Comparison logic error: {e}")
        else:
            st.info("Select at least one metric to view comparison.")
    else:
        st.warning("'flowline_Shakers' column not found in dataset.")
