import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA RESPONSIVA Y PREMIUM DARK MODE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Dashboard - Costos & Margen",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# ESTILOS CSS AVANZADOS (INTERFAZ MODERNA & CONTRASTE)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        /* Fondo General Dark Mode */
        .stApp {
            background-color: #0B0E14;
            color: #E2E8F0;
        }
        
        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }

        /* Banner Informativo de Mes */
        .month-banner {
            background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
            border-left: 4px solid #38BDF8;
            padding: 10px 16px;
            border-radius: 6px;
            margin-bottom: 18px;
            font-size: 0.9rem;
            color: #94A3B8;
        }
        .month-banner strong {
            color: #38BDF8;
        }

        /* Tarjeta KPI Premium */
        .kpi-card {
            background: linear-gradient(135deg, #1E293B 0%, #111827 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .kpi-card:hover {
            border-color: #38BDF8;
            transform: translateY(-2px);
        }
        .kpi-title {
            color: #94A3B8;
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .kpi-value {
            color: #4ADE80;
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .kpi-sub {
            color: #22C55E;
            font-size: 0.78rem;
            margin-top: 4px;
            font-weight: 500;
        }
        .kpi-neutral { color: #38BDF8 !important; }
        .kpi-warning { color: #FBBF24 !important; }

        /* Estilizado de Dataframes/Tablas Dark Mode */
        [data-testid="stDataFrame"] {
            background-color: #1E293B !important;
            border-radius: 8px;
            border: 1px solid #334155;
            padding: 6px;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0F172A;
            border-right: 1px solid #1E293B;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# CARGA Y PREPROCESAMIENTO DE DATOS CON MES DE VENTA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df_ventas = pd.read_excel("VENTAS.xlsx", header=7)
    df_receta = pd.read_excel("RECETA.xlsx")
    df_precios = pd.read_excel("PRECIOS.xlsx")

    # Estandarizar nombre de columna
    df_ventas.rename(columns={"ART": "Cod. Venta"}, inplace=True)

    # Convertir Fechas y extraer 'Mes_Venta' (YYYY-MM)
    if "FECHA" in df_ventas.columns:
        df_ventas["FECHA"] = pd.to_datetime(df_ventas["FECHA"], errors="coerce")
        df_ventas["Mes_Venta"] = df_ventas["FECHA"].dt.strftime("%Y-%m")
    else:
        df_ventas["Mes_Venta"] = "Sin Fecha"

    if "Mes" in df_receta.columns:
        df_receta["Mes"] = pd.to_datetime(df_receta["Mes"], errors="coerce")
        df_receta["Mes_Str"] = df_receta["Mes"].dt.strftime("%Y-%m")
    else:
        df_receta["Mes_Str"] = "Sin Fecha"

    if "Mes" in df_precios.columns:
        df_precios["Mes"] = pd.to_datetime(df_precios["Mes"], errors="coerce")
        df_precios["Mes_Str"] = df_precios["Mes"].dt.strftime("%Y-%m")
    else:
        df_precios["Mes_Str"] = "Sin Fecha"

    # Conversiones numéricas
    for df in [df_ventas, df_receta]:
        df["Cod. Venta"] = pd.to_numeric(df["Cod. Venta"], errors="coerce")

    for df in [df_receta, df_precios]:
        df["Código Insumo"] = pd.to_numeric(
            df["Código Insumo"], errors="coerce"
        )

    df_ventas = df_ventas.dropna(subset=["Cod. Venta"])
    df_receta = df_receta.dropna(subset=["Cod. Venta", "Código Insumo"])

    # Cruce Receta + Precios
    receta_precios = pd.merge(
        df_receta,
        df_precios[["Código Insumo", "Descripción", "Precio Compra"]],
        on="Código Insumo",
        how="left",
    )
    receta_precios["Costo Insumo ($)"] = (
        receta_precios["Cant. Teorica"] * receta_precios["Precio Compra"]
    )

    return df_ventas, df_receta, df_precios, receta_precios


df_ventas, df_receta, df_precios, receta_precios = load_data()


# Componente HTML para KPIs
def draw_kpi(title, value, sub="", color_class=""):
    val_class = f"kpi-value {color_class}".strip()
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="{val_class}">{value}</div>
        {sub_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def truncate_text(text, max_len=28):
    text = str(text)
    return text[:max_len] + "..." if len(text) > max_len else text


plotly_config = {"responsive": True, "displayModeBar": False}

# ---------------------------------------------------------
# SIDEBAR / NAVEGACIÓN Y FILTRO POR MES
# ---------------------------------------------------------
st.sidebar.title("⚡ Control Center")
vista = st.sidebar.radio(
    "Seleccionar Vista:",
    ["🔎 Análisis por Producto", "🌐 Visión General de Compañía"],
)

st.sidebar.divider()
st.sidebar.header("🗓️ Filtro de Período")

# Obtener meses disponibles
meses_disponibles = sorted(
    list(set(df_ventas["Mes_Venta"].dropna().unique()))
)
if not meses_disponibles or meses_disponibles == ["Sin Fecha"]:
    meses_disponibles = ["Todos los Meses"]

opciones_mes = ["Todos los Meses"] + [
    m for m in meses_disponibles if m != "Todos los Meses"
]
mes_seleccionado = st.sidebar.selectbox("Mes de Venta / Costos:", opciones_mes)

# Filtrado de Ventas por Mes
if mes_seleccionado != "Todos los Meses":
    df_ventas_filt = df_ventas[df_ventas["Mes_Venta"] == mes_seleccionado]
else:
    df_ventas_filt = df_ventas.copy()

st.sidebar.divider()

if vista == "🔎 Análisis por Producto":
    st.sidebar.header("📦 Filtro de Producto")

    articulos_df = (
        df_receta[["Cod. Venta", "Artículo"]]
        .drop_duplicates()
        .sort_values("Artículo")
    )
    opciones_dict = {
        f"{int(row['Cod. Venta'])} - {row['Artículo']}": int(row["Cod. Venta"])
        for _, row in articulos_df.iterrows()
    }

    item_seleccionado = st.sidebar.selectbox(
        "Seleccionar Artículo:", list(opciones_dict.keys())
    )
    cod_art = opciones_dict[item_seleccionado]
    nombre_art = item_seleccionado.split(" - ")[1]

    # Receta e Insumos
    receta_prod = receta_precios[receta_precios["Cod. Venta"] == cod_art].copy()
    costo_unitario = receta_prod["Costo Insumo ($)"].sum()

    # Ventas filtradas
    ventas_prod = df_ventas_filt[df_ventas_filt["Cod. Venta"] == cod_art]
    volumen_unid = (
        ventas_prod["Físicos"].sum() if "Físicos" in ventas_prod.columns else 0
    )
    fact_lista = (
        ventas_prod["Facturación Lista"].sum()
        if "Facturación Lista" in ventas_prod.columns
        else 0
    )
    fact_neta = (
        ventas_prod["Facturación Neta"].sum()
        if "Facturación Neta" in ventas_prod.columns
        else 0
    )

    costo_total_prod = costo_unitario * volumen_unid
    contribucion_marg = fact_neta - costo_total_prod
    pct_margen = (
        (contribucion_marg / fact_neta * 100) if fact_neta > 0 else 0.0
    )
    descuento_comercial = fact_lista - fact_neta
    precio_prom_unit = (fact_neta / volumen_unid) if volumen_unid > 0 else 0.0

    # ---------------------------------------------------------
    # HEADER Y BANNER DE MES DE VENTA
    # ---------------------------------------------------------
    st.title(f"📦 {nombre_art}")

    # Banner con el mes explícito
    st.markdown(
        f"""
        <div class="month-banner">
            📅 Período Evaluado: <strong>Mes de Venta {mes_seleccionado}</strong> | Código de Venta: <strong>{cod_art}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🚀 Indicadores Clave (KPIs)")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        draw_kpi(
            "Costo Teórico Unit.",
            f"${costo_unitario:,.2f}",
            color_class="kpi-warning",
        )
    with col2:
        draw_kpi(
            "Volumen Vendido",
            f"{volumen_unid:,.0f} u.",
            color_class="kpi-neutral",
        )
    with col3:
        draw_kpi("Facturación Neta", f"${fact_neta:,.2f}")
    with col4:
        draw_kpi(
            "Costo Total Prod.",
            f"${costo_total_prod:,.2f}",
            color_class="kpi-warning",
        )
    with col5:
        draw_kpi(
            "Margen Contribución",
            f"{pct_margen:.1f}%",
            sub=f"+${contribucion_marg:,.0f}",
        )

    col6, col7, col8, col9 = st.columns(4)
    with col6:
        draw_kpi(
            "Precio Prom. Real",
            f"${precio_prom_unit:,.2f}",
            color_class="kpi-neutral",
        )
    with col7:
        draw_kpi("Facturación Lista", f"${fact_lista:,.2f}")
    with col8:
        draw_kpi(
            "Descuento Comercial",
            f"${descuento_comercial:,.2f}",
            color_class="kpi-warning",
        )
    with col9:
        draw_kpi(
            "Insumos en Receta",
            f"{len(receta_prod)} Insumos",
            color_class="kpi-neutral",
        )

    st.divider()

    # ---------------------------------------------------------
    # GRÁFICOS INTERACTIVOS
    # ---------------------------------------------------------
    st.markdown("### 📊 Composición y Distribución de Costos")
    col_g1, col_g2 = st.columns([3, 2])

    with col_g1:
        if not receta_prod.empty:
            df_sorted = receta_prod.sort_values(
                "Costo Insumo ($)", ascending=True
            ).copy()
            df_sorted["Insumo_Label"] = df_sorted["Descripción"].apply(
                lambda x: truncate_text(x, 28)
            )

            fig_bar = px.bar(
                df_sorted,
                x="Costo Insumo ($)",
                y="Insumo_Label",
                orientation="h",
                text="Costo Insumo ($)",
                template="plotly_dark",
                color="Costo Insumo ($)",
                color_continuous_scale="Viridis",
                title="Ranking de Insumos por Costo ($)",
            )
            fig_bar.update_traces(
                texttemplate="$%{x:,.2f}", textposition="outside"
            )
            fig_bar.update_layout(
                showlegend=False,
                margin=dict(l=10, r=40, t=35, b=10),
                height=380,
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#0B0E14",
                xaxis_title="",
                yaxis_title="",
                coloraxis_showscale=False,
            )
            st.plotly_chart(
                fig_bar, use_container_width=True, config=plotly_config
            )

    with col_g2:
        if not receta_prod.empty and costo_unitario > 0:
            receta_prod_copy = receta_prod.copy()
            receta_prod_copy["Insumo_Label"] = receta_prod_copy[
                "Descripción"
            ].apply(lambda x: truncate_text(x, 20))

            fig_pie = px.pie(
                receta_prod_copy,
                names="Insumo_Label",
                values="Costo Insumo ($)",
                hole=0.45,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold,
                title="Distribución % Insumos",
            )
            fig_pie.update_traces(
                textposition="inside", textinfo="percent+label"
            )
            fig_pie.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=35, b=10),
                height=380,
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#0B0E14",
            )
            st.plotly_chart(
                fig_pie, use_container_width=True, config=plotly_config
            )

    st.divider()

    # ---------------------------------------------------------
    # TABLA DESGLOSE (BOM) Y BARRAS DE IMPACTO
    # ---------------------------------------------------------
    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        st.markdown("### 📋 Desglose de Receta (BOM)")
        tabla_out = receta_prod[
            [
                "Código Insumo",
                "Descripción",
                "Cant. Teorica",
                "Precio Compra",
                "Costo Insumo ($)",
            ]
        ].copy()
        tabla_out["% Part."] = (
            tabla_out["Costo Insumo ($)"] / costo_unitario * 100
            if costo_unitario > 0
            else 0
        )
        tabla_out.columns = [
            "Cód. Insumo",
            "Insumo",
            "Cant. Teórica",
            "Precio Unit. ($)",
            "Costo ($)",
            "% Participación",
        ]

        st.dataframe(
            tabla_out.style.format(
                {
                    "Cant. Teórica": "{:,.4f}",
                    "Precio Unit. ($)": "${:,.2f}",
                    "Costo ($)": "${:,.2f}",
                    "% Participación": "{:.1f}%",
                }
            ),
            use_container_width=True,
            height=340,
        )

    with col_t2:
        st.markdown("### 📊 Contribución al Costo Total")
        if not receta_prod.empty:
            df_flujo = receta_prod.sort_values(
                "Costo Insumo ($)", ascending=True
            ).copy()
            df_flujo["Insumo_Corto"] = df_flujo["Descripción"].apply(
                lambda x: truncate_text(x, 24)
            )

            fig_flujo = px.bar(
                df_flujo,
                x="Costo Insumo ($)",
                y="Insumo_Corto",
                orientation="h",
                text="Costo Insumo ($)",
                template="plotly_dark",
                color="Costo Insumo ($)",
                color_continuous_scale="Greens",
            )
            fig_flujo.update_traces(
                texttemplate="$%{x:,.2f}", textposition="outside"
            )
            fig_flujo.update_layout(
                showlegend=False,
                margin=dict(l=10, r=40, t=20, b=10),
                height=340,
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#0B0E14",
                xaxis_title="Costo ($)",
                yaxis_title="",
                coloraxis_showscale=False,
            )
            st.plotly_chart(
                fig_flujo, use_container_width=True, config=plotly_config
            )

else:
    # ---------------------------------------------------------
    # VISTA GENERAL DE COMPAÑÍA CON FILTRO DE MES
    # ---------------------------------------------------------
    st.title("🌐 Visión General Consolidada")

    st.markdown(
        f"""
        <div class="month-banner">
            📅 Consolidados correspondientes al <strong>Mes de Venta: {mes_seleccionado}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    costo_por_art = (
        receta_precios.groupby("Cod. Venta")["Costo Insumo ($)"]
        .sum()
        .reset_index()
    )
    costo_por_art.rename(
        columns={"Costo Insumo ($)": "Costo Unitario ($)"}, inplace=True
    )

    df_ventas_merged = pd.merge(
        df_ventas_filt, costo_por_art, on="Cod. Venta", how="left"
    )
    df_ventas_merged["Costo Unitario ($)"] = df_ventas_merged[
        "Costo Unitario ($)"
    ].fillna(0)
    df_ventas_merged["Costo Total Ventas ($)"] = (
        df_ventas_merged["Físicos"] * df_ventas_merged["Costo Unitario ($)"]
    )
    df_ventas_merged["Margen Bruto ($)"] = (
        df_ventas_merged["Facturación Neta"]
        - df_ventas_merged["Costo Total Ventas ($)"]
    )

    tot_fact_neta = df_ventas_merged["Facturación Neta"].sum()
    tot_costo_ventas = df_ventas_merged["Costo Total Ventas ($)"].sum()
    tot_margen = tot_fact_neta - tot_costo_ventas
    tot_volumen = df_ventas_merged["Físicos"].sum()
    pct_margen_global = (
        (tot_margen / tot_fact_neta * 100) if tot_fact_neta > 0 else 0
    )

    gk1, gk2, gk3, gk4 = st.columns(4)
    with gk1:
        draw_kpi("Facturación Global", f"${tot_fact_neta:,.2f}")
    with gk2:
        draw_kpi(
            "Costo Insumos",
            f"${tot_costo_ventas:,.2f}",
            color_class="kpi-warning",
        )
    with gk3:
        draw_kpi(
            "Margen Bruto",
            f"${tot_margen:,.2f}",
            sub=f"{pct_margen_global:.1f}% Margen",
        )
    with gk4:
        draw_kpi(
            "Volumen Total", f"{tot_volumen:,.0f} u.", color_class="kpi-neutral"
        )

    st.divider()

    col_g_left, col_g_right = st.columns(2)

    with col_g_left:
        st.markdown("### 🌳 Insumos de Mayor Impacto Global")
        df_global_insumos = pd.merge(
            df_receta,
            df_ventas_filt[["Cod. Venta", "Físicos"]],
            on="Cod. Venta",
        )
        df_global_insumos = pd.merge(
            df_global_insumos,
            df_precios[["Código Insumo", "Descripción", "Precio Compra"]],
            on="Código Insumo",
        )
        df_global_insumos["Gasto Total Insumo ($)"] = (
            df_global_insumos["Cant. Teorica"]
            * df_global_insumos["Físicos"]
            * df_global_insumos["Precio Compra"]
        )

        insumos_summary = (
            df_global_insumos.groupby("Descripción")["Gasto Total Insumo ($)"]
            .sum()
            .reset_index()
        )
        insumos_summary["Insumo_Corto"] = insumos_summary["Descripción"].apply(
            lambda x: truncate_text(x, 24)
        )

        fig_tree = px.treemap(
            insumos_summary,
            path=["Insumo_Corto"],
            values="Gasto Total Insumo ($)",
            template="plotly_dark",
            color="Gasto Total Insumo ($)",
            color_continuous_scale="Plasma",
        )
        fig_tree.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            height=380,
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#0B0E14",
        )
        st.plotly_chart(
            fig_tree, use_container_width=True, config=plotly_config
        )

    with col_g_right:
        st.markdown("### 🏆 Top 10 Productos por Facturación")
        top_ventas = (
            df_ventas_merged.groupby("Nombre")["Facturación Neta"]
            .sum()
            .reset_index()
            .sort_values("Facturación Neta", ascending=False)
            .head(10)
        )
        top_ventas["Nombre_Corto"] = top_ventas["Nombre"].apply(
            lambda x: truncate_text(x, 22)
        )

        fig_top = px.bar(
            top_ventas,
            x="Facturación Neta",
            y="Nombre_Corto",
            orientation="h",
            template="plotly_dark",
            color="Facturación Neta",
            color_continuous_scale="Cividis",
        )
        fig_top.update_layout(
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,
            height=380,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#0B0E14",
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(
            fig_top, use_container_width=True, config=plotly_config
        )
