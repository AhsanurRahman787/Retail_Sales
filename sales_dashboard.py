import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import calendar
import numpy as np

st.set_page_config(page_title="Sales Analytics Dashboard", layout="wide")
st.title("📊 Sales Analytics Dashboard (2014–2017)")

# File uploader (XLSX only)
uploaded_file = st.file_uploader("Upload your cleaned **Excel file (.xlsx)**", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)

        # Ensure required columns
        required_cols = ['order_date', 'customer_name', 'product_name', 'channel', 'state', 'revenue', 'total_cost']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            st.error(f"❌ Missing columns: {missing}")
        else:
            df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
            df = df.dropna(subset=['order_date'])
            df = df[(df['order_date'].dt.year >= 2014) & (df['order_date'].dt.year <= 2017)]
            df['profit'] = df['revenue'] - df['total_cost']
            df['profit_margin_pct'] = (df['profit'] / df['revenue']) * 100

            st.success(f"✅ Loaded {len(df)} orders.")

            # --- TOGGLE BUTTON ---
            single_view = st.toggle(".Toggle Single View", value=False)

            # List of analysis options
            analysis_options = [
                "📈 Monthly Sales Trend",
                "💰 Top Products",
                "📊 Unit Price Distribution",
                "🏆 Top States",
                "📐 Profit Margin by Channel",
                "👑 Top/Bottom Customers",
                "🔍 Customer Segmentation",
                "🔥 Correlation Heatmap"
            ]

            if single_view:
                # Single view: dropdown to select one analysis
                selected = st.selectbox("Choose analysis", analysis_options)
                analysis_list = [selected]
            else:
                # Multi-tab view
                analysis_list = analysis_options

            # Render selected analyses
            for analysis in analysis_list:
                st.subheader(analysis)

                if analysis == "📈 Monthly Sales Trend":
                    df['month'] = df['order_date'].dt.month
                    monthly_sales = df.groupby('month')['revenue'].sum().reindex(range(1, 13), fill_value=0)
                    month_names = [calendar.month_abbr[i] for i in range(1, 13)]
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(month_names, monthly_sales.values, marker='o', linestyle='-', color='b')
                    ax.set_ylabel("Revenue ($)")
                    ax.grid(True, linestyle='--', alpha=0.6)
                    st.pyplot(fig)

                elif analysis == "💰 Top Products":
                    product_rev = df.groupby('product_name')['revenue'].sum().sort_values(ascending=False).head(15)
                    fig = px.bar(product_rev, x=product_rev.index, y=product_rev.values, labels={'y': 'Revenue ($)'})
                    st.plotly_chart(fig, use_container_width=True)

                elif analysis == "📊 Unit Price Distribution":
                    if 'order_quantity' in df.columns:
                        df['unit_price'] = df['revenue'] / df['order_quantity']
                        top_products = df['product_name'].value_counts().index[:10]
                        df_top = df[df['product_name'].isin(top_products)]
                        fig, ax = plt.subplots(figsize=(12, 6))
                        sns.boxplot(data=df_top, x='product_name', y='unit_price', ax=ax)
                        plt.xticks(rotation=45, ha='right')
                        st.pyplot(fig)
                    else:
                        st.info("⚠️ `order_quantity` missing → unit price not computed.")

                elif analysis == "🏆 Top States":
                    state_metrics = df.groupby('state').agg(total_revenue=('revenue', 'sum'), order_count=('revenue', 'count'))
                    col1, col2 = st.columns(2)
                    with col1:
                        top_rev = state_metrics.nlargest(10, 'total_revenue')
                        fig = px.bar(top_rev, x=top_rev.index, y='total_revenue', title="Top 10 by Revenue")
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        top_orders = state_metrics.nlargest(10, 'order_count')
                        fig = px.bar(top_orders, x=top_orders.index, y='order_count', title="Top 10 by Orders")
                        st.plotly_chart(fig, use_container_width=True)

                elif analysis == "📐 Profit Margin by Channel":
                    margin_by_channel = df.groupby('channel')['profit_margin_pct'].mean().sort_values(ascending=False)
                    fig, ax = plt.subplots()
                    bars = ax.bar(margin_by_channel.index, margin_by_channel.values, color='teal')
                    for bar in bars:
                        h = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2, h + 0.5, f'{h:.1f}%', ha='center', va='bottom')
                    ax.set_ylabel("Avg Profit Margin (%)")
                    st.pyplot(fig)

                elif analysis == "👑 Top/Bottom Customers":
                    cust_rev = df.groupby('customer_name')['revenue'].sum().sort_values(ascending=False)
                    col1, col2 = st.columns(2)
                    with col1:
                        top = cust_rev.head(10)
                        fig = px.bar(top, x=top.index, y=top.values, title="Top 10 Customers")
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        bottom = cust_rev.tail(10)
                        fig = px.bar(bottom, x=bottom.index, y=bottom.values, title="Bottom 10 Customers")
                        st.plotly_chart(fig, use_container_width=True)

                elif analysis == "🔍 Customer Segmentation":
                    cust_summary = df.groupby('customer_name').agg(
                        total_revenue=('revenue', 'sum'),
                        avg_profit_margin=('profit_margin_pct', 'mean'),
                        order_count=('revenue', 'count')
                    ).reset_index()
                    fig = px.scatter(
                        cust_summary,
                        x='total_revenue',
                        y='avg_profit_margin',
                        size='order_count',
                        hover_name='customer_name',
                        color='total_revenue',
                        title="Bubble size = Order Count"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif analysis == "🔥 Correlation Heatmap":
                    numeric_cols = ['revenue', 'total_cost', 'profit', 'profit_margin_pct']
                    if 'order_quantity' in df.columns:
                        numeric_cols.append('order_quantity')
                    if 'unit_price' in df.columns:
                        numeric_cols.append('unit_price')
                    numeric_df = df[numeric_cols]
                    corr = numeric_df.corr()
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', square=True, ax=ax)
                    st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error: {e}")

else:
    st.info("👈 Upload an **.xlsx** file to begin.")