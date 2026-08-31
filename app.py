import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA RESPONSIVA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Dashboard - Costos & Margen",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# ESTILOS CSS (DARK MODE & CORRECCIÓN DE TABLAS/KPIS)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        /* Fondo principal */
        .stApp {
            background-color: #0E1117;
            color: #E0E6ED;
        }
        
        /* Ajuste padding contenedor */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }

        /* Tarjeta KPI estilizada */
        .kpi-card {
            background: linear-gradient(135deg, #1E222D 0%, #171A21 100%);
            border: 1px solid #2A303C;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 12px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.35);
        }
        .kpi-title {
            color: #9AA8B8;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .kpi-value {
            color: #00E676;
            font-size: 1.4rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .kpi-sub {
            color: #4CAF50;
            font-size: 0.78rem;
            margin-top: 4px;
            font-weight: 500;
        }
        .kpi-neutral { color: #29B6F6 !important; }
        .kpi-warning { color: #FFB74D !important; }

        /* Corrección estricta para tablas en Modo Oscuro (Elimina bloques blancos) */
        [data-testid="stDataFrame"] {
            background-color: #1E222D !important;
            border-radius: 8px;
            border: 1px solid #2A303C;
            padding: 6px;
        }
        
        /* Estilizado del Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #131722;
            border-right: 1px solid #2A303C;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# CARGA Y PREPROCESAMIENTO DE DATOS
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df_ventas = pd.read_excel("VENTAS.xlsx", header=7)
    df_receta = pd.read_excel("RECETA.xlsx")
    df_precios = pd.read_excel("PRECIOS.xlsx")
    df_teoricos = pd.read_excel("TEORICOS.xlsx", header=6)

    df_ventas.rename(columns={"ART": "Cod. Venta"}, inplace=True)

    for df in [df_ventas, df_receta, df_teoricos]:
        df["Cod. Venta"] = pd.to_numeric(df["Cod. Venta"], errors="coerce")

    for df in [df_receta, df_precios]:
        df["Código Insumo"] = pd.to_numeric(
            df["Código Insumo"], errors="coerce"
        )

    df_ventas = df_ventas.dropna(subset=["Cod. Venta"])
    df_receta = df_receta.dropna(subset=["Cod. Venta", "Código Insumo"])

    receta_precios = pd.merge(
        df_receta,
        df_precios[["Código Insumo", "Descripción", "Precio Compra"]],
        on="Código Insumo",
        how="left",
    )
    receta_precios["Costo Insumo ($)"] = (
        receta_precios["Cant. Teorica"] * receta_precios["Precio Compra"]
    )

    return df_ventas, df_receta, df_precios, df_teoricos, receta_precios


df_ventas, df_receta, df_precios, df_teoricos, receta_precios = load_data()


# Función HTML para renderizar KPIs
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
# NAVEGACIÓN Y FILTROS
# ---------------------------------------------------------
st.sidebar.title("⚡ Control Center")
vista = st.sidebar.radio(
    "Seleccionar Vista:",
    ["🔎 Análisis por Producto", "🌐 Visión General de Compañía"],
)

st.sidebar.divider()

if vista == "🔎 Análisis por Producto":
    st.sidebar.header("Filtros")

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

    # Cálculos por Producto
    receta_prod = receta_precios[receta_precios["Cod. Venta"] == cod_art].copy()
    costo_unitario = receta_prod["Costo Insumo ($)"].sum()

    ventas_prod = df_ventas[df_ventas["Cod. Venta"] == cod_art]
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
    # ENCABEZADO Y KPIS
    # ---------------------------------------------------------
    st.title(f"📦 {nombre_art}")
    st.caption(
        f"Código de Venta: **{cod_art}** | Estructura Teórica e Indicadores"
    )

    # Fila 1 KPIs
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

    # Fila 2 KPIs
    col6, col7, col8, col9 = st.columns(4)
    with col6:
        draw_kpi(
            "Precio Prom. Unit.",
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
            "Cant. Insumos",
            f"{len(receta_prod)} Insumos",
            color_class="kpi-neutral",
        )

    st.divider()

    # ---------------------------------------------------------
    # GRÁFICOS PRINCIPALES
    # ---------------------------------------------------------
    st.markdown("### 📊 Composición y Distribución de Costos")
    col_g1, col_g2 = st.columns([3, 2])

    with col_g1:
        if not receta_prod.empty:
            df_sorted = receta_prod.sort_values(
                "Costo Insumo ($)", ascending=True
            ).copy()
            df_sorted["Insumo_Label"] = df_sorted["Descripción"].apply(
                lambda x: truncate_text(x, 30)
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
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
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
            ].apply(lambda x: truncate_text(x, 22))

            fig_pie = px.pie(
                receta_prod_copy,
                names="Insumo_Label",
                values="Costo Insumo ($)",
                hole=0.45,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold,
                title="Distribución Percentual",
            )
            fig_pie.update_traces(
                textposition="inside", textinfo="percent+label"
            )
            fig_pie.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=35, b=10),
                height=380,
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
            )
            st.plotly_chart(
                fig_pie, use_container_width=True, config=plotly_config
            )

    st.divider()

    # ---------------------------------------------------------
    # TABLA DE DETALLE (BOM) Y SEGUNDO GRÁFICO HORIZONTAL
    # ---------------------------------------------------------
    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        st.markdown("### 📋 Desglose de Receta (Bill of Materials)")
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
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
                xaxis_title="Costo ($)",
                yaxis_title="",
                coloraxis_showscale=False,
            )
            st.plotly_chart(
                fig_flujo, use_container_width=True, config=plotly_config
            )

else:
    # ---------------------------------------------------------
    # VISTA GENERAL DE LA COMPAÑÍA
    # ---------------------------------------------------------
    st.title("🌐 Visión General Consolidada")

    costo_por_art = (
        receta_precios.groupby("Cod. Venta")["Costo Insumo ($)"]
        .sum()
        .reset_index()
    )
    costo_por_art.rename(
        columns={"Costo Insumo ($)": "Costo Unitario ($)"}, inplace=True
    )

    df_ventas_merged = pd.merge(
        df_ventas, costo_por_art, on="Cod. Venta", how="left"
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
            df_receta, df_ventas[["Cod. Venta", "Físicos"]], on="Cod. Venta"
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
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
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
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(
            fig_top, use_container_width=True, config=plotly_config
        )
