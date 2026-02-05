import streamlit as st

def apply_premium_style():
    """
    套用全域 Premium 樣式 (極致暗色 / Cyberpunk AI)
    基於 @ui-ux-pro-max Skill 規範優化
    """
    st.markdown("""
        <style>
        /* =========================================
           1. GLOBAL SCALE & BACKGROUND
        ========================================= */
        html {
            font-size: 110%;
        }
        
        .stApp {
            background: linear-gradient(180deg, #0E1117 0%, #06080A 100%);
            background-attachment: fixed;
            color: #E0E0E0;
        }
        
        .stApp::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(14, 17, 23, 0.7);
            z-index: -1;
        }

        /* =========================================
           2. TYPOGRAPHY (Accessibility Compliant)
           - min 4.5:1 contrast ratio
           - line-height 1.5-1.75
        ========================================= */
        p, .stMarkdown, .stText, .stCode, .stSelectbox label, .stTextInput label {
            font-size: 1.2rem !important;
            font-weight: 500;
            line-height: 1.6;
            color: #E6EDF3; /* Improved contrast - 9.3:1 on dark bg */
        }
        
        h1 { font-size: 3rem !important; color: #FFFFFF; }
        h2 { font-size: 2.4rem !important; color: #F0F6FC; }
        h3 { font-size: 1.8rem !important; color: #E6EDF3; }
        
        /* Muted text must be at least slate-400 */
        .stCaption, small, .stRadio label span {
            color: #8B949E !important; /* 5.1:1 contrast */
        }

        /* =========================================
           3. SIDEBAR
        ========================================= */
        [data-testid="stSidebar"] {
            background: rgba(22, 27, 34, 0.95);
            border-right: 1px solid #30363D;
        }

        /* =========================================
           4. GLASSMORPHISM CARDS
        ========================================= */
        .diag-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%);
            border: 1px solid rgba(88, 166, 255, 0.2);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
            cursor: pointer;
        }
        .diag-card:hover {
            transform: translateY(-2px);
            border-color: rgba(88, 166, 255, 0.5);
            box-shadow: 0 4px 30px rgba(88, 166, 255, 0.1);
        }

        /* =========================================
           5. METRICS & SAA OUTPUT
        ========================================= */
        [data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
            color: #58A6FF;
            text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
        }
        
        .saa-cmd {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 1.1rem;
            color: #7EE787;
            background: rgba(13, 17, 23, 0.8);
            border: 1px solid #30363D;
            padding: 4px 8px;
            border-radius: 6px;
        }

        /* =========================================
           6. TABS
        ========================================= */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            border-bottom: 1px solid #30363D;
        }
        .stTabs [data-baseweb="tab"] {
            height: 60px;
            white-space: pre-wrap;
            font-weight: 700;
            font-size: 1.2rem;
            color: #8B949E;
            transition: color 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #C9D1D9;
        }
        .stTabs [aria-selected="true"] {
            color: #58A6FF !important;
            border-bottom-color: #58A6FF !important;
        }

        /* =========================================
           7. BUTTONS (Premium + Loading States)
           - cursor pointer on all interactive
           - smooth transitions 150-300ms
           - disabled state styling
        ========================================= */
        .stButton button {
            font-size: 1.2rem !important;
            padding: 0.6rem 1.2rem !important;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(88, 166, 255, 0.2);
        }
        
        .stButton button:active:not(:disabled) {
            transform: translateY(0);
        }
        
        .stButton button:disabled {
            cursor: not-allowed;
            opacity: 0.6;
        }
        
        /* Primary button style */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #238636 0%, #2EA043 100%);
            border: none;
        }

        /* =========================================
           8. INPUTS & FORMS
           - visible focus states
           - proper labels
        ========================================= */
        .stTextInput input, .stSelectbox > div > div {
            border-radius: 8px;
            border: 1px solid #30363D;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        
        .stTextInput input:focus, .stSelectbox > div > div:focus-within {
            border-color: #58A6FF;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.3);
            outline: none;
        }

        /* =========================================
           9. SPINNER / LOADING STATES
        ========================================= */
        .stSpinner > div {
            border-top-color: #58A6FF !important;
        }

        /* =========================================
           10. GRADIENT TEXT ANIMATION
        ========================================= */
        .premium-text {
            background: linear-gradient(90deg, #58A6FF 0%, #238636 50%, #BC8CFF 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            animation: gradient 5s linear infinite;
        }
        
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* =========================================
           11. ACCESSIBILITY: REDUCED MOTION
        ========================================= */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

def render_premium_header(title: str, subtitle: str):
    """渲染具有設計感的頁頭"""
    st.markdown(f'# <span class="premium-text">{title}</span>', unsafe_allow_html=True)
    st.markdown(f"#### {subtitle}")
    st.markdown("---")
