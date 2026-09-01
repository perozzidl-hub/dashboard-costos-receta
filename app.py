import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILO LIMPIO
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Ventas & Costos",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stApp {
            background-color: #0F172A;
            color: #F8FAFC;
        }
        .main-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-bottom: 0.2rem;
        }
        .sub-title {
            color: #94A3B8;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }
        .kpi-card {
            background-color: #1E293B;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #334155;
            text-align: center;
        }
        .kpi-label {
            color: #94A3B8;
            font-size: 0.82rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .kpi-value {
            color: #F8FAFC;
            font-size: 1.5rem;
            font-weight: 700;
            margin-top: 4px;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# CARGA DE DATOS REALES (CON CACHÉ)
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    try:
        df_ventas = pd.read_excel("VENTAS.xlsx", header=7)
    except Exception:
        df_ventas = pd.DataFrame()

    try:
        df_receta = pd.read_excel("RECETA.xlsx")
    except Exception:
        df_receta = pd.DataFrame()

    try:
        df_precios = pd.read_excel("PRECIOS.xlsx")
    except Exception:
        df_precios = pd.DataFrame()

    if not df_ventas.empty:
        df_ventas.rename(columns={"ART": "Cod. Venta"}, inplace=True)

        if "FECHA" in df_ventas.columns:
            df_ventas["FECHA"] = pd.to_datetime(
                df_ventas["FECHA"], errors="coerce"
            )
            df_ventas["Mes_Venta"] = df_ventas["FECHA"].dt.strftime("%Y-%m")
        else:
            df_ventas["Mes_Venta"] = "Sin Fecha"

        col_tipo = None
        for col in df_ventas.columns:
            if any(
                k in str(col).lower()
                for k in ["tipo", "origen", "propio", "reventa", "clasif"]
            ):
                col_tipo = col
                break

        df_ventas["Tipo_Producto"] = (
            df_ventas[col_tipo].astype(str).str.strip().str.upper()
            if col_tipo
            else "P"
        )
        df_ventas["Cod. Venta"] = pd.to_numeric(
            df_ventas["Cod. Venta"], errors="coerce"
        )
        df_ventas = df_ventas.dropna(subset=["Cod. Venta"])

        for col in ["TOTAL INSUMOS", "TOTAL PRODUCTO TERCEROS", "Físicos", "Facturación Neta"]:
            if col in df_ventas.columns:
                df_ventas[col] = pd.to_numeric(df_ventas[col], errors="coerce").fillna(0.0)
            else:
                df_ventas[col] = 0.0

        df_ventas["COSTO_TOTAL_REAL"] = df_ventas.apply(
            lambda r: r["TOTAL PRODUCTO TERCEROS"]
            if r["Tipo_Producto"] == "R"
            else r["TOTAL INSUMOS"],
            axis=1,
        )

    return df_ventas, df_receta, df_precios


df_ventas, df_receta, df_precios = load_data()

if df_ventas.empty:
    st.error("⚠️ No se pudieron cargar los datos de VENTAS.xlsx. Por favor revisa la ruta o formato del archivo.")
    st.stop()

# ---------------------------------------------------------
# FILTROS SIMPLES EN SIDEBAR
# ---------------------------------------------------------
st.sidebar.header("🔍 Filtros de Control")

vista = st.sidebar.radio(
    "Nivel de Análisis:",
    ["Análisis por Producto", "Visión General de Compañía"],
)

st.sidebar.divider()

meses_disponibles = sorted([m for m in df_ventas["Mes_Venta"].unique() if m != "Sin Fecha"])
opciones_mes = ["Todos los Meses"] + meses_disponibles
mes_seleccionado = st.sidebar.selectbox("Seleccionar Mes:", opciones_mes)

# Filtrado inicial por mes
df_filt = df_ventas.copy()
if mes_seleccionado != "Todos los Meses":
    df_filt = df_filt[df_filt["Mes_Venta"] == mes_seleccionado]


# ---------------------------------------------------------
# VISTA 1: ANÁLISIS POR PRODUCTO
# ---------------------------------------------------------
if vista == "Análisis por Producto":
    col_nombre = "Nombre" if "Nombre" in df_ventas.columns else ("Artículo" if "Artículo" in df_ventas.columns else "Cod. Venta")
    
    articulos_df = df_filt[["Cod. Venta", col_nombre]].drop_duplicates().sort_values(col_nombre)
    
    if articulos_df.empty:
        st.warning("No hay productos disponibles para el filtro seleccionado.")
        st.stop()

    opciones_prod = {
        f"{int(r['Cod. Venta'])} - {r[col_nombre]}": int(r["Cod. Venta"])
        for _, r in articulos_df.iterrows()
    }
    
    prod_seleccionado = st.sidebar.selectbox("Producto:", list(opciones_prod.keys()))
    cod_art = opciones_prod[prod_seleccionado]
    nombre_art = prod_seleccionado.split(" - ")[1] if " - " in prod_seleccionado else prod_seleccionado

    # Datos históricos completos del producto (para la línea de tiempo) y filtrados
    df_prod_hist = df_ventas[df_ventas["Cod. Venta"] == cod_art]
    df_prod_mes = df_filt[df_filt["Cod. Venta"] == cod_art]

    # Métricas del período
    volumen = df_prod_mes["Físicos"].sum()
    facturacion = df_prod_mes["Facturación Neta"].sum()
    costo_total = df_prod_mes["COSTO_TOTAL_REAL"].sum()
    contribucion = facturacion - costo_total

    fact_unit = (facturacion / volumen) if volumen > 0 else 0.0
    costo_unit = (costo_total / volumen) if volumen > 0 else 0.0
    contrib_unit = fact_unit - costo_unit

    # Encabezado
    st.markdown(f'<div class="main-title">📦 {nombre_art} (Código: {cod_art})</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">Período: {mes_seleccionado}</div>', unsafe_allow_html=True)

    # 4 Tarjetas de Resumen
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Facturación Unit.</div><div class="kpi-value">${fact_unit:,.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Costo Unitario</div><div class="kpi-value" style="color:#FBBF24;">${costo_unit:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Contribución Unit.</div><div class="kpi-value" style="color:#38BDF8;">${contrib_unit:,.2f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Unidades Vendidas</div><div class="kpi-value" style="color:#4ADE80;">{volumen:,.0f} u.</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Evolución Mensual Unitario ($/u)")

    # Agrupamiento estricto por Mes-Año para la evolución temporal
    evol_prod = (
        df_prod_hist.groupby("Mes_Venta")
        .agg({"Facturación Neta": "sum", "COSTO_TOTAL_REAL": "sum", "Físicos": "sum"})
        .reset_index()
        .sort_values("Mes_Venta")
    )

    if not evol_prod.empty and len(evol_prod) > 1:
        evol_prod["Fact_Unit"] = evol_prod.apply(lambda r: r["Facturación Neta"] / r["Físicos"] if r["Físicos"] > 0 else 0, axis=1)
        evol_prod["Costo_Unit"] = evol_prod.apply(lambda r: r["COSTO_TOTAL_REAL"] / r["Físicos"] if r["Físicos"] > 0 else 0, axis=1)
        evol_prod["Contrib_Unit"] = evol_prod["Fact_Unit"] - evol_prod["Costo_Unit"]

        fig = go.Figure()
        
        # Facturación Unit.
        fig.add_trace(go.Scatter(
            x=evol_prod["Mes_Venta"], y=evol_prod["Fact_Unit"],
            name="Facturación Unit. ($)", mode="lines+markers",
            line=dict(color="#4ADE80", width=3), marker=dict(size=8)
        ))
        
        # Costo Unitario
        fig.add_trace(go.Scatter(
            x=evol_prod["Mes_Venta"], y=evol_prod["Costo_Unit"],
            name="Costo Unitario ($)", mode="lines+markers",
            line=dict(color="#FBBF24", width=3), marker=dict(size=8)
        ))

        # Contribución Unitaria
        fig.add_trace(go.Scatter(
            x=evol_prod["Mes_Venta"], y=evol_prod["Contrib_Unit"],
            name="Contribución Unit. ($)", mode="lines+markers",
            line=dict(color="#38BDF8", width=3, dash="dot"), marker=dict(size=8)
        ))

        fig.update_layout(
            template="plotly_dark",
            height=380,
            paper_bgcolor="#0F172A",
            plot_bgcolor="#0F172A",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            xaxis=dict(type="category", title="Mes / Año", gridcolor="#334155"),
            yaxis=dict(title="Monto ($ / Unidad)", gridcolor="#334155")
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Se requiere información de más de 1 mes para mostrar la gráfica de evolución.")


# ---------------------------------------------------------
# VISTA 2: VISIÓN GENERAL DE COMPAÑÍA
# ---------------------------------------------------------
else:
    st.markdown('<div class="main-title">🌐 Visión General Consolidada de Compañía</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">Período: {mes_seleccionado}</div>', unsafe_allow_html=True)

    fact_tot = df_filt["Facturación Neta"].sum()
    costo_tot = df_filt["COSTO_TOTAL_REAL"].sum()
    contrib_tot = fact_tot - costo_tot
    vol_tot = df_filt["Físicos"].sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Facturación Global</div><div class="kpi-value">${fact_tot:,.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Costo Total</div><div class="kpi-value" style="color:#FBBF24;">${costo_tot:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Contribución Total</div><div class="kpi-value" style="color:#38BDF8;">${contrib_tot:,.2f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Unidades Totales</div><div class="kpi-value" style="color:#4ADE80;">{vol_tot:,.0f} u.</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Evolución Histórica de la Empresa ($)")

    evol_glob = (
        df_ventas.groupby("Mes_Venta")
        .agg({"Facturación Neta": "sum", "COSTO_TOTAL_REAL": "sum"})
        .reset_index()
        .sort_values("Mes_Venta")
    )

    if not evol_glob.empty and len(evol_glob) > 1:
        evol_glob["Contribución"] = evol_glob["Facturación Neta"] - evol_glob["COSTO_TOTAL_REAL"]

        fig_glob = go.Figure()

        fig_glob.add_trace(go.Scatter(
            x=evol_glob["Mes_Venta"], y=evol_glob["Facturación Neta"],
            name="Facturación Total ($)", mode="lines+markers",
            line=dict(color="#4ADE80", width=3), marker=dict(size=8)
        ))

        fig_glob.add_trace(go.Scatter(
            x=evol_glob["Mes_Venta"], y=evol_glob["COSTO_TOTAL_REAL"],
            name="Costo Total ($)", mode="lines+markers",
            line=dict(color="#FBBF24", width=3), marker=dict(size=8)
        ))

        fig_glob.add_trace(go.Scatter(
            x=evol_glob["Mes_Venta"], y=evol_glob["Contribución"],
            name="Contribución ($)", mode="lines+markers",
            line=dict(color="#38BDF8", width=3, dash="dot"), marker=dict(size=8)
        ))

        fig_glob.update_layout(
            template="plotly_dark",
            height=380,
            paper_bgcolor="#0F172A",
            plot_bgcolor="#0F172A",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            xaxis=dict(type="category", title="Mes / Año", gridcolor="#334155"),
            yaxis=dict(title="Monto Total ($)", gridcolor="#334155")
        )

        st.plotly_chart(fig_glob, use_container_width=True)
    else:
        st.info("ℹ️ Se requiere información de más de 1 mes para mostrar la gráfica consolidada.")
