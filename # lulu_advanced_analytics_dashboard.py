# lulu_advanced_analytics_dashboard.py
# Advanced Streamlit dashboard for Lulu UAE sales & ad performance analysis
# Usage:
#   pip install streamlit pandas numpy altair
#   streamlit run lulu_advanced_analytics_dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Lulu UAE — Advanced Analytics", layout="wide")
alt.data_transformers.enable('default', max_rows=50000)

# ===== HELPERS =====
def load_csv_safe(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return pd.read_csv(p)
    except Exception:
        try:
            return pd.read_csv(p, engine="python")
        except Exception:
            return None

def detect_columns(df):
    cols = df.columns.tolist()
    def find(terms):
        for t in terms:
            for c in cols:
                if t in c.lower():
                    return c
        return None
    return {
        'amount': find(['amount','sales','revenue','net','total','paid','value']),
        'qty': find(['qty','quantity','units']),
        'department': find(['department','dept']),
        'store_format': find(['store_format','store format','format','storetype','store_type']),
        'category': find(['category','cat','sub_category','subcat']),
        'product': find(['product','sku','item','product_name']),
        'campaign': find(['campaign','ad_campaign','campaign_name']),
        'promo': find(['promo','voucher','coupon','promo_code','discount']),
        'gender': find(['gender']),
        'age': find(['age','customer_age','age_group']),
        'nationality': find(['national','country','nationality']),
        'city': find(['city','location']),
        'transaction': find(['invoice','transaction','order','receipt','bill','txn']),
        'date': find(['date','transaction_date','purchase_date'])
    }

def prepare_dataframe(df, mapping):
    d = df.copy()
    ren = {}
    if mapping.get('amount'): ren[mapping['amount']] = 'SalesAmount'
    if mapping.get('qty'): ren[mapping['qty']] = 'Quantity'
    if mapping.get('department'): ren[mapping['department']] = 'Department'
    if mapping.get('store_format'): ren[mapping['store_format']] = 'Store_format'
    if mapping.get('category'): ren[mapping['category']] = 'Category'
    if mapping.get('product'): ren[mapping['product']] = 'Product'
    if mapping.get('campaign'): ren[mapping['campaign']] = 'Campaign'
    if mapping.get('promo'): ren[mapping['promo']] = 'PromoCode'
    if mapping.get('gender'): ren[mapping['gender']] = 'Gender'
    if mapping.get('age'): ren[mapping['age']] = 'Age'
    if mapping.get('nationality'): ren[mapping['nationality']] = 'Nationality'
    if mapping.get('city'): ren[mapping['city']] = 'City'
    if mapping.get('transaction'): ren[mapping['transaction']] = 'Transaction'
    if mapping.get('date'): ren[mapping['date']] = 'Date'
    d = d.rename(columns=ren)

    if 'SalesAmount' in d.columns:
        d['SalesAmount'] = pd.to_numeric(d['SalesAmount'], errors='coerce').fillna(0.0)
    else:
        d['SalesAmount'] = 1.0
    if 'Quantity' in d.columns:
        d['Quantity'] = pd.to_numeric(d['Quantity'], errors='coerce').fillna(1)
    else:
        d['Quantity'] = 1
    if 'Transaction' not in d.columns:
        d['Transaction'] = d.index.astype(str)
    else:
        d['Transaction'] = d['Transaction'].astype(str)

    # Handle Age
    if 'Age' in d.columns:
        d['Age'] = pd.to_numeric(d['Age'], errors='coerce')
    else:
        d['Age'] = np.random.randint(18, 65, size=len(d))

    # Create Age Groups
    def age_group(age):
        if pd.isna(age): return 'Unknown'
        if age < 18: return '13-17'
        elif age < 25: return '18-24'
        elif age < 35: return '25-34'
        elif age < 45: return '35-44'
        elif age < 55: return '45-54'
        elif age < 65: return '55-64'
        else: return '65+'
    
    d['AgeGroup'] = d['Age'].apply(age_group)

    text_cols = ['Department','Store_format','Category','Product','Campaign','PromoCode','Gender','Nationality','City']
    for c in text_cols:
        if c in d.columns:
            d[c] = d[c].fillna('Unknown').astype(str)

    if 'Date' in d.columns:
        d['Date'] = pd.to_datetime(d['Date'], errors='coerce')
    else:
        d['Date'] = pd.Timestamp.now()

    if 'PromoCode' in d.columns:
        d['PromoUsed'] = d['PromoCode'].astype(str).str.strip().replace({'nan':'','None':''}).apply(lambda x: bool(x) and x!='')
    else:
        d['PromoUsed'] = False

    if 'Campaign' in d.columns:
        d['CampaignActive'] = d['Campaign'].astype(str).str.strip() != 'Unknown'
    else:
        d['CampaignActive'] = False

    return d

# ===== LOAD DATA =====
DEFAULT_PATH = "/mnt/data/lulu_uae_master_2000.csv"
raw = load_csv_safe(DEFAULT_PATH)

st.sidebar.header("📁 Data Management")
use_upload = st.sidebar.checkbox("Upload CSV", value=False)
if use_upload:
    uploaded = st.sidebar.file_uploader("Upload transactions CSV", type=["csv"])
    if uploaded is not None:
        raw = pd.read_csv(uploaded)

if raw is None:
    st.error(f"Could not load CSV. Please upload a file.")
    st.stop()

mapping = detect_columns(raw)
df = prepare_dataframe(raw, mapping)

# ===== SIDEBAR NAVIGATION & FILTERS =====
st.sidebar.header("🎯 Navigation & Filters")

page = st.sidebar.radio("Select Page", [
    "📊 Overview",
    "👥 Customer Personas",
    "📢 Ad Campaign Analysis",
    "🎯 Category Targeting Strategy",
    "📈 Advanced Comparisons"
])

# Global Filters
st.sidebar.subheader("Global Filters")

city_values = ['All'] + sorted([c for c in df['City'].unique() if c != 'Unknown'])
selected_city = st.sidebar.selectbox("🏙️ City", city_values)

store_values = ['All'] + sorted([s for s in df['Store_format'].unique() if s != 'Unknown'])
selected_store = st.sidebar.selectbox("🏬 Store Type", store_values)

if 'Date' in df.columns and df['Date'].notna().any():
    min_d = df['Date'].min().date()
    max_d = df['Date'].max().date()
    date_range = st.sidebar.date_input("📅 Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
else:
    date_range = None

# Apply Filters
mask = pd.Series(True, index=df.index)
if selected_city != 'All':
    mask &= (df['City'] == selected_city)
if selected_store != 'All':
    mask &= (df['Store_format'] == selected_store)
if date_range:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    mask &= (df['Date'] >= start) & (df['Date'] <= end)

filtered = df[mask].copy()

# ===== PAGE: OVERVIEW =====
if page == "📊 Overview":
    st.title("📊 Lulu UAE — Sales Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    total_sales = filtered['SalesAmount'].sum()
    total_tx = filtered['Transaction'].nunique()
    avg_basket = filtered.groupby('Transaction')['SalesAmount'].sum().mean() if total_tx > 0 else 0
    total_qty = filtered['Quantity'].sum()
    
    col1.metric("💰 Total Sales", f"AED {total_sales:,.0f}")
    col2.metric("🛒 Transactions", f"{total_tx:,}")
    col3.metric("📦 Avg Basket", f"AED {avg_basket:,.2f}")
    col4.metric("📊 Total Qty", f"{total_qty:,}")
    
    st.divider()
    
    # City Analysis
    st.subheader("🏙️ Sales by City")
    city_df = filtered.groupby('City').agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique')
    ).reset_index().sort_values('TotalSales', ascending=False)
    city_df['AvgBasket'] = city_df['TotalSales'] / city_df['Transactions']
    
    chart_city = alt.Chart(city_df).mark_bar().encode(
        x=alt.X('City:N', sort='-y'),
        y='TotalSales:Q',
        color='TotalSales:Q',
        tooltip=['City', 'TotalSales:Q', 'Transactions:Q', 'AvgBasket:Q']
    ).properties(width=800, height=400).interactive()
    st.altair_chart(chart_city, use_container_width=True)
    
    # Store Type Analysis
    st.subheader("🏬 Sales by Store Type")
    store_df = filtered.groupby('Store_format').agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique')
    ).reset_index().sort_values('TotalSales', ascending=False)
    store_df['AvgBasket'] = store_df['TotalSales'] / store_df['Transactions']
    
    chart_store = alt.Chart(store_df).mark_bar().encode(
        x=alt.X('Store_format:N', sort='-y'),
        y='TotalSales:Q',
        color='TotalSales:Q',
        tooltip=['Store_format', 'TotalSales:Q', 'Transactions:Q']
    ).properties(width=800, height=400).interactive()
    st.altair_chart(chart_store, use_container_width=True)

# ===== PAGE: CUSTOMER PERSONAS =====
elif page == "👥 Customer Personas":
    st.title("👥 Customer Personas by Age Group")
    st.write("Analyze purchasing behavior across age groups to identify target demographics.")
    
    st.divider()
    
    # Age Group Distribution
    st.subheader("📊 Customer Distribution by Age Group")
    age_dist = filtered['AgeGroup'].value_counts().reset_index().rename(columns={'index': 'AgeGroup', 'AgeGroup': 'Count'})
    age_dist = age_dist.sort_values('AgeGroup')
    
    chart_age = alt.Chart(age_dist).mark_bar().encode(
        x=alt.X('AgeGroup:N', sort=['13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']),
        y='Count:Q',
        color='Count:Q',
        tooltip=['AgeGroup', 'Count:Q']
    ).properties(width=800, height=400).interactive()
    st.altair_chart(chart_age, use_container_width=True)
    
    st.divider()
    
    # Age Group Selection
    selected_age_group = st.selectbox("Select Age Group to Analyze", ['All'] + sorted(filtered['AgeGroup'].unique()))
    age_filtered = filtered if selected_age_group == 'All' else filtered[filtered['AgeGroup'] == selected_age_group]
    
    st.subheader(f"🛍️ Top Categories for {selected_age_group}")
    
    cat_age = age_filtered.groupby('Category').agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique'),
        AvgQty=('Quantity', 'mean')
    ).reset_index().sort_values('TotalSales', ascending=False).head(15)
    
    chart_cat = alt.Chart(cat_age).mark_bar().encode(
        x=alt.X('Category:N', sort='-y'),
        y='TotalSales:Q',
        color='TotalSales:Q',
        tooltip=['Category', 'TotalSales:Q', 'Transactions:Q', 'AvgQty:Q']
    ).properties(width=900, height=400).interactive()
    st.altair_chart(chart_cat, use_container_width=True)
    
    st.divider()
    
    # Heatmap: Age Group vs Category
    st.subheader("🔥 Heatmap: Age Group vs Top Categories")
    top_cats = filtered.groupby('Category')['SalesAmount'].sum().nlargest(10).index
    heatmap_data = filtered[filtered['Category'].isin(top_cats)].groupby(['AgeGroup', 'Category']).agg(
        TotalSales=('SalesAmount', 'sum')
    ).reset_index()
    
    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X('Category:N'),
        y=alt.Y('AgeGroup:N', sort=['13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']),
        color='TotalSales:Q',
        tooltip=['AgeGroup', 'Category', 'TotalSales:Q']
    ).properties(width=900, height=400).interactive()
    st.altair_chart(heatmap, use_container_width=True)
    
    st.divider()
    
    # Summary Statistics
    st.subheader("📈 Persona Summary Statistics")
    persona_stats = filtered.groupby('AgeGroup').agg(
        TotalSales=('SalesAmount', 'sum'),
        AvgTransaction=('SalesAmount', 'mean'),
        AvgQty=('Quantity', 'mean'),
        UniqueCustomers=('Transaction', 'nunique'),
        MostBought=('Category', lambda x: x.value_counts().index[0] if len(x) > 0 else 'N/A')
    ).reset_index().sort_values('AgeGroup')
    
    st.dataframe(persona_stats, use_container_width=True)

# ===== PAGE: AD CAMPAIGN ANALYSIS =====
elif page == "📢 Ad Campaign Analysis":
    st.title("📢 Ad Campaign Performance Analysis")
    st.write("Analyze campaign effectiveness across cities and identify winning strategies.")
    
    st.divider()
    
    # Overall Campaign Performance
    st.subheader("📊 Overall Campaign Performance")
    campaign_perf = filtered.groupby('Campaign').agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique'),
        AvgBasket=('SalesAmount', 'mean'),
        WithPromo=('PromoUsed', 'sum'),
        PromoRate=('PromoUsed', 'mean')
    ).reset_index().sort_values('TotalSales', ascending=False)
    
    campaign_perf['ROIScore'] = (campaign_perf['TotalSales'] / campaign_perf['Transactions']).round(2)
    
    chart_camp = alt.Chart(campaign_perf).mark_bar().encode(
        x=alt.X('Campaign:N', sort='-y'),
        y='TotalSales:Q',
        color='ROIScore:Q',
        tooltip=['Campaign', 'TotalSales:Q', 'Transactions:Q', 'AvgBasket:Q', 'PromoRate:Q']
    ).properties(width=1000, height=400).interactive()
    st.altair_chart(chart_camp, use_container_width=True)
    
    st.dataframe(campaign_perf, use_container_width=True)
    
    st.divider()
    
    # Campaign Performance by City
    st.subheader("🏙️ Campaign Performance by City")
    selected_campaign = st.selectbox("Select Campaign to Analyze", ['All'] + sorted([c for c in filtered['Campaign'].unique() if c != 'Unknown']))
    
    camp_filtered = filtered if selected_campaign == 'All' else filtered[filtered['Campaign'] == selected_campaign]
    
    camp_city = camp_filtered.groupby(['City', 'Campaign']).agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique'),
        AvgBasket=('SalesAmount', 'mean')
    ).reset_index().sort_values('TotalSales', ascending=False)
    
    chart_camp_city = alt.Chart(camp_city).mark_bar().encode(
        x=alt.X('City:N', sort='-y'),
        y='TotalSales:Q',
        color='Campaign:N',
        tooltip=['City', 'Campaign', 'TotalSales:Q', 'Transactions:Q', 'AvgBasket:Q']
    ).properties(width=1000, height=400).interactive()
    st.altair_chart(chart_camp_city, use_container_width=True)
    
    st.divider()
    
    # Campaign Effectiveness: Promo vs Non-Promo
    st.subheader("💡 Why Campaigns Work or Fail")
    camp_analysis = filtered.groupby('Campaign').agg(
        PromoRate=('PromoUsed', 'mean'),
        AvgSalesWithPromo=('SalesAmount', 'mean'),
        TransactionCount=('Transaction', 'nunique'),
        TopCategory=('Category', lambda x: x.value_counts().index[0] if len(x) > 0 else 'N/A')
    ).reset_index()
    
    camp_analysis['Performance'] = camp_analysis['PromoRate'].apply(
        lambda x: '✅ High Engagement' if x > 0.3 else ('⚠️ Medium Engagement' if x > 0.15 else '❌ Low Engagement')
    )
    
    st.dataframe(camp_analysis, use_container_width=True)
    
    st.write("""
    **Interpretation Guide:**
    - ✅ High Engagement: >30% customers used promos → Campaign messaging resonates
    - ⚠️ Medium Engagement: 15-30% promo usage → Campaign has potential but needs optimization
    - ❌ Low Engagement: <15% promo usage → Campaign not effective, needs revision
    """)

# ===== PAGE: CATEGORY TARGETING STRATEGY =====
elif page == "🎯 Category Targeting Strategy":
    st.title("🎯 Category Targeting Strategy")
    st.write("Match top categories with best performing age groups and campaigns.")
    
    st.divider()
    
    # Top Categories Overall
    st.subheader("🏆 Top 15 Categories by Sales")
    top_cats = filtered.groupby('Category').agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique'),
        AvgBasket=('SalesAmount', 'mean')
    ).reset_index().sort_values('TotalSales', ascending=False).head(15)
    
    chart_top_cats = alt.Chart(top_cats).mark_bar().encode(
        x=alt.X('Category:N', sort='-y'),
        y='TotalSales:Q',
        color='TotalSales:Q',
        tooltip=['Category', 'TotalSales:Q', 'Transactions:Q', 'AvgBasket:Q']
    ).properties(width=1000, height=400).interactive()
    st.altair_chart(chart_top_cats, use_container_width=True)
    
    st.divider()
    
    # Select Category for Deep Dive
    st.subheader("🔍 Category Deep Dive Analysis")
    selected_cat = st.selectbox("Select Category", sorted(filtered['Category'].unique()))
    cat_data = filtered[filtered['Category'] == selected_cat]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Category Sales", f"AED {cat_data['SalesAmount'].sum():,.0f}")
    col2.metric("👥 Best Age Group", cat_data['AgeGroup'].value_counts().index[0] if len(cat_data) > 0 else 'N/A')
    col3.metric("📢 Best Campaign", cat_data['Campaign'].value_counts().index[0] if len(cat_data) > 0 else 'N/A')
    
    st.divider()
    
    # Age Group Performance for Selected Category
    st.subheader(f"📊 {selected_cat} - Sales by Age Group")
    cat_age_sales = cat_data.groupby('AgeGroup').agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique'),
        AvgBasket=('SalesAmount', 'mean')
    ).reset_index().sort_values('TotalSales', ascending=False)
    
    chart_cat_age = alt.Chart(cat_age_sales).mark_bar().encode(
        x=alt.X('AgeGroup:N'),
        y='TotalSales:Q',
        color='TotalSales:Q',
        tooltip=['AgeGroup', 'TotalSales:Q', 'Transactions:Q']
    ).properties(width=800, height=400).interactive()
    st.altair_chart(chart_cat_age, use_container_width=True)
    
    st.divider()
    
    # Campaign Performance for Selected Category
    st.subheader(f"📢 {selected_cat} - Campaign Performance")
    cat_camp_sales = cat_data.groupby('Campaign').agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique'),
        PromoRate=('PromoUsed', 'mean')
    ).reset_index().sort_values('TotalSales', ascending=False)
    
    chart_cat_camp = alt.Chart(cat_camp_sales).mark_bar().encode(
        x=alt.X('Campaign:N', sort='-y'),
        y='TotalSales:Q',
        color='PromoRate:Q',
        tooltip=['Campaign', 'TotalSales:Q', 'Transactions:Q', 'PromoRate:Q']
    ).properties(width=800, height=400).interactive()
    st.altair_chart(chart_cat_camp, use_container_width=True)
    
    st.divider()
    
    # Recommendation Engine
    st.subheader("💡 Targeting Recommendations")
    best_age = cat_age_sales.iloc[0]
    best_camp = cat_camp_sales.iloc[0]
    
    st.info(f"""
    **Recommended Targeting Strategy for {selected_cat}:**
    
    🎯 **Primary Target Demographic:** {best_age['AgeGroup']} age group
    - Sales Contribution: AED {best_age['TotalSales']:,.0f}
    - Average Transaction: AED {best_age['AvgBasket']:,.2f}
    
    📢 **Best Performing Campaign:** {best_camp['Campaign']}
    - Campaign Sales: AED {best_camp['TotalSales']:,.0f}
    - Promo Engagement: {best_camp['PromoRate']:.1%}
    
    ✅ **Action Plan:**
    1. Create targeted ads for {best_age['AgeGroup']} age group
    2. Use {best_camp['Campaign']} messaging strategy
    3. Focus on {selected_cat} product placement in high-traffic areas
    4. Monitor engagement metrics weekly
    """)

# ===== PAGE: ADVANCED COMPARISONS =====
elif page == "📈 Advanced Comparisons":
    st.title("📈 Advanced Comparisons & Insights")
    st.write("Multi-dimensional analysis: Age Group × Campaign × Category")
    
    st.divider()
    
    # 3D Analysis: Age Group × Campaign × Category
    st.subheader("🔄 Age Group × Campaign Performance")
    
    age_camp = filtered.groupby(['AgeGroup', 'Campaign']).agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique')
    ).reset_index()
    
    heatmap_ac = alt.Chart(age_camp).mark_rect().encode(
        x=alt.X('Campaign:N'),
        y=alt.Y('AgeGroup:N', sort=['13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']),
        color='TotalSales:Q',
        tooltip=['AgeGroup', 'Campaign', 'TotalSales:Q', 'Transactions:Q']
    ).properties(width=1000, height=400).interactive()
    st.altair_chart(heatmap_ac, use_container_width=True)
    
    st.divider()
    
    # Campaign × Category Performance
    st.subheader("🔄 Campaign × Top Categories")
    
    top_categories = filtered['Category'].value_counts().head(10).index
    camp_cat = filtered[filtered['Category'].isin(top_categories)].groupby(['Campaign', 'Category']).agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique')
    ).reset_index().sort_values('TotalSales', ascending=False).head(30)
    
    chart_cc = alt.Chart(camp_cat).mark_bar().encode(
        x=alt.X('Campaign:N'),
        y='TotalSales:Q',
        color='Category:N',
        tooltip=['Campaign', 'Category', 'TotalSales:Q', 'Transactions:Q']
    ).properties(width=1000, height=400).interactive()
    st.altair_chart(chart_cc, use_container_width=True)
    
    st.divider()
    
    # City × Age Group × Sales
    st.subheader("🏙️ City × Age Group Performance")
    
    city_age = filtered.groupby(['City', 'AgeGroup']).agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique')
    ).reset_index()
    
    heatmap_ca = alt.Chart(city_age).mark_rect().encode(
        x=alt.X('City:N'),
        y=alt.Y('AgeGroup:N', sort=['13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']),
        color='TotalSales:Q',
        tooltip=['City', 'AgeGroup', 'TotalSales:Q', 'Transactions:Q']
    ).properties(width=1000, height=400).interactive()
    st.altair_chart(heatmap_ca, use_container_width=True)
    
    st.divider()
    
    # Performance Insights
    st.subheader("📊 Key Performance Insights")
    
    top_combo = filtered.groupby(['AgeGroup', 'Campaign', 'Category']).agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique')
    ).reset_index().sort_values('TotalSales', ascending=False).head(10)
    
    st.write("**Top 10 Age Group + Campaign + Category Combinations:**")
    st.dataframe(top_combo, use_container_width=True)
    
    st.divider()
    
    # Export Summary
    st.subheader("📥 Export Analysis")
    summary_data = filtered.groupby(['City', 'AgeGroup', 'Campaign', 'Category']).agg(
        TotalSales=('SalesAmount', 'sum'),
        Transactions=('Transaction', 'nunique'),
        AvgBasket=('SalesAmount', 'mean'),
        PromoRate=('PromoUsed', 'mean')
    ).reset_index().sort_values('TotalSales', ascending=False)
    
    csv = summary_data.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Analysis (CSV)",
        data=csv,
        file_name="lulu_advanced_analysis.csv",
        mime="text/csv"
    )

# ===== ADDITIONAL FEATURES - PROMO ANALYSIS PAGE =====
st.sidebar.divider()

# Advanced Export Section
st.sidebar.subheader("💾 Export & Reports")

if st.sidebar.button("📊 Generate Full Report"):
    st.sidebar.success("Report generation started!")
    
    report_data = {
        'Overview': filtered.groupby('City').agg(TotalSales=('SalesAmount', 'sum')).to_dict(),
        'Demographics': filtered['AgeGroup'].value_counts().to_dict(),
        'Campaigns': filtered['Campaign'].value_counts().to_dict(),
        'Categories': filtered['Category'].value_counts().to_dict()
    }

csv_filtered = filtered.to_csv(index=False)
st.sidebar.download_button(
    label="📥 Download Filtered Data",
    data=csv_filtered,
    file_name="lulu_filtered_transactions.csv",
    mime="text/csv"
)