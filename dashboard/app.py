import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(
    page_title="RevenueCore Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #eef3f8;
        border-bottom: 2px solid #4e8cff;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# --- API ---
API_URL = "http://127.0.0.1:8000"

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=100)
    st.title("RevenueCore")
    st.caption("Intelligent Pricing & Recommendation Engine")
    st.markdown("---")
    st.markdown("### ⚙️ System Status")
    
    # Kiểm tra kết nối API
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            st.success("API: Online 🟢")
        else:
            st.error("API: Error 🔴")
    except:
        st.error("API: Offline 🔴")

    st.info("Model: LightGBM + FP-Growth")
    st.markdown("---")
    
    # --- PHẦN LOGS MỚI ---
    st.markdown("### 📝 Activity Logs")
    
    log_text = "Connecting to logs..."
    try:
        # Gọi API lấy logs
        log_res = requests.get(f"{API_URL}/logs")
        if log_res.status_code == 200:
            logs = log_res.json().get("logs", [])
            # Nối các dòng log lại thành 1 chuỗi
            log_text = "\n".join(logs)
    except:
        log_text = "Could not fetch logs."

    # Hiển thị log trong text_area
    st.text_area("Recent Actions", log_text, height=200, disabled=True)

# --- MAIN HEADER ---
st.title("📊 Executive Dashboard")
st.markdown("Welcome back, **Admin**. Here is your revenue optimization overview.")
st.markdown("---")

# --- TABS ---
tab1, tab2 = st.tabs(["💰 Dynamic Pricing Engine", "🛒 Smart Recommendations"])

# --- TAB 1: PRICING ---
with tab1:
    col_left, col_right = st.columns([1, 2], gap="large")
    
    with col_left:
        st.subheader("🔧 Configuration")
        with st.container(border=True):
            st.markdown("**Target Product**")
            product_id = st.number_input("Enter Product ID", value=9662, step=1, help="Unique identifier for the product")
            
            if st.button("🚀 Optimize Price", type="primary", use_container_width=True):
                with st.spinner("Analyzing market data..."):
                    try:
                        response = requests.post(f"{API_URL}/optimize", json={"product_id": int(product_id)})
                        if response.status_code == 200:
                            st.session_state['pricing_data'] = response.json()
                            st.toast("Optimization Complete!", icon="✅")
                        else:
                            st.error(f"API Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

        if 'pricing_data' in st.session_state:
            data = st.session_state['pricing_data']
            st.subheader("📈 Key Metrics")
            
            # Custom Metric Cards
            st.markdown(f"""
            <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                <div style="flex: 1; background: #e3f2fd; padding: 10px; border-radius: 8px; text-align: center;">
                    <small style="color: black;">Current Price</small>
                    <h3 style="margin: 0; color: #1565c0;">${data['current_price']}</h3>
                </div>
                <div style="flex: 1; background: #e8f5e9; padding: 10px; border-radius: 8px; text-align: center;">
                    <small style="color: black;">Optimal Price</small>
                    <h3 style="margin: 0; color: #2e7d32;">${data['optimal_price']}</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.metric("Revenue Uplift", data['revenue_uplift'], delta=data['revenue_uplift'], delta_color="normal")
            st.caption(f"Predicted Revenue: ${data['predicted_revenue']}")

    with col_right:
        st.subheader("📊 Demand Simulation")
        if 'pricing_data' in st.session_state:
            data = st.session_state['pricing_data']
            curr = data['current_price']
            opt = data['optimal_price']
            rev = data['predicted_revenue']
            
            # Simulation Data Generation
            sim_data = []
            factors = [0.7, 0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3]
            for f in factors:
                p = curr * f
                dist = abs(p - opt)
                # Parabolic simulation centered at optimal
                r = rev - (dist * 5) - (dist**2 * 0.5) 
                sim_data.append({"Price": p, "Revenue": r})
            
            df_chart = pd.DataFrame(sim_data).sort_values("Price")
            
            # Plotly Chart
            fig = go.Figure()
            
            # Revenue Curve
            fig.add_trace(go.Scatter(
                x=df_chart['Price'], y=df_chart['Revenue'],
                mode='lines', name='Revenue Curve',
                line=dict(color='#4e8cff', width=3, shape='spline')
            ))
            
            # Current Price Point
            curr_rev = rev - (abs(curr - opt) * 5) - (abs(curr - opt)**2 * 0.5)
            fig.add_trace(go.Scatter(
                x=[curr], y=[curr_rev],
                mode='markers', name='Current Price',
                marker=dict(size=12, color='red', symbol='x')
            ))
            
            # Optimal Price Point
            fig.add_trace(go.Scatter(
                x=[opt], y=[rev],
                mode='markers', name='Optimal Price',
                marker=dict(size=15, color='green', symbol='star')
            ))

            fig.update_layout(
                title="Price vs. Revenue Analysis",
                xaxis_title="Price ($)",
                yaxis_title="Predicted Revenue ($)",
                template="plotly_white",
                hovermode="x unified",
                height=500,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("👈 Run optimization to view the analysis chart.")
            # Placeholder image
            st.markdown("""
                <div style="text-align: center; padding: 50px; background: #f0f2f6; border-radius: 10px;">
                    <h3 style="color: #bdc3c7;">Chart Area</h3>
                    <p style="color: #95a5a6;">Data visualization will appear here after analysis.</p>
                </div>
            """, unsafe_allow_html=True)

# --- TAB 2: RECSYS ---
with tab2:
    st.subheader("🛍️ Cross-Selling Recommendations")
    
    col_input, col_res = st.columns([1, 2])
    
    with col_input:
        st.markdown("### Customer Cart")
        demo_items = ['bed_bath_table', 'computers_accessories', 'furniture_decor', 'watches_gifts', 'health_beauty', 'sports_leisure']
        selected_items = st.multiselect("Select items in cart:", demo_items, default=['bed_bath_table'])
        
        if st.button("🔍 Get Recommendations", type="primary", use_container_width=True):
            if not selected_items:
                st.warning("Please select at least one item.")
            else:
                with st.spinner("Finding best matches..."):
                    try:
                        response = requests.post(f"{API_URL}/recommend", json={"cart_items": selected_items})
                        if response.status_code == 200:
                            st.session_state['recsys_data'] = response.json()
                        else:
                            st.error(f"API Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

    with col_res:
        if 'recsys_data' in st.session_state:
            res = st.session_state['recsys_data']
            recs = res.get('recommendations', [])
            
            if recs:
                st.success(f"Found {len(recs)} recommendations based on {len(res['input_cart'])} items.")
                
                # Display as cards
                for item in recs:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"### ⭐ {item['Product']}")
                            st.caption(item['Reason'])
                        with c2:
                            conf = item['Confidence']
                            st.metric("Confidence", f"{conf*100:.1f}%")
                            st.progress(min(float(conf), 1.0))
            else:
                st.warning("No strong recommendations found for this combination.")
        else:
            st.info("Select items and click 'Get Recommendations' to see results.")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <small>RevenueCore © 2025 | Powered by LightGBM </small>
    </div>
    """, unsafe_allow_html=True
)