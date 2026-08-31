import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA EN DARK MODE PROFESIONAL
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Cost & Margin Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS avanzados para corregir contraste, tablas y KPIs
st.markdown(
    """
    <style>
        /* Fondo general */
        .stApp {
            background-color: #0E1117;
            color: #E0E6ED;
        }
        
        /* Ocultar barra superior genérica */
        header[data-testid="stHeader"] {
            background-color: #0E1117;
        }

        /* Tarjeta KPI en Dark Mode */
        .kpi-card {
            background: linear-gradient(135deg, #1E222D 0%, #171A21 100%);
            border: 1px solid #2A303C;
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .kpi-card:hover {
            border-color: #00E676;
            transform: translateY(-2px);
        }
        .kpi-title {
            color: #8C9BAE;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .kpi-value {
            color: #00E676;
            font-size: 1.6rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .kpi-sub {
            color: #4CAF50;
            font-size: 0.8rem;
            margin-top: 4px;
            font-weight: 500;
        }
        .kpi-value-neutral {
            color: #29B6F6;
        }
        .kpi-value-warning {
            color: #FFB74D;
        }

        /* Ajustes Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #131722;
            border-right: 1px solid #2A303C;
        }

        /* Estilo de Dataframes/Tablas en Modo Oscuro */
        [data-testid="stDataFrame"] {
            background-color: #1E222D;
            border-radius: 8px;
            padding: 8px;
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

    # Renombrar columna clave en ventas
    df_ventas.rename(columns={"ART": "Cod. Venta"}, inplace=True)

    # Conversión estricta a numérico
    for df in [df_ventas, df_receta, df_teoricos]:
        df["Cod. Venta"] = pd.to_numeric(df["Cod. Venta"], errors="coerce")

    for df in [df_receta, df_precios]:
        df["Código Insumo"] = pd.to_numeric(
            df["Código Insumo"], errors="coerce"
        )

    # Limpieza
    df_ventas = df_ventas.dropna(subset=["Cod. Venta"])
    df_receta = df_receta.dropna(subset=["Cod. Venta", "Código Insumo"])

    # Cruce maestro Receta + Precios
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


# Componente HTML para Tarjetas KPI legibles
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


# ---------------------------------------------------------
# SIDEBAR / NAVEGACIÓN
# ---------------------------------------------------------
st.sidebar.title("⚡ Control Center")
vista = st.sidebar.radio(
    "Seleccionar Vista:",
    ["🔎 Análisis por Producto", "🌐 Visión General de Compañía"],
)

st.sidebar.divider()

if vista == "🔎 Análisis por Producto":
    st.sidebar.header("Filtro de Producto")

    # Lista de productos ordenada
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

    # Cálculos específicos
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
    # HEADER Y KPIS
    # ---------------------------------------------------------
    st.title(f"📦 {nombre_art}")
    st.caption(
        f"Código de Venta: **{cod_art}** | Tablero de Estructura de Costos y Rentabilidad"
    )

    st.markdown("### 🚀 Indicadores Clave (KPIs)")

    # Fila 1 de KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        draw_kpi(
            "Costo Teórico Unitario",
            f"${costo_unitario:,.2f}",
            color_class="kpi-value-warning",
        )
    with col2:
        draw_kpi(
            "Volumen Vendido",
            f"{volumen_unid:,.0f} u.",
            color_class="kpi-value-neutral",
        )
    with col3:
        draw_kpi("Facturación Neta", f"${fact_neta:,.2f}")
    with col4:
        draw_kpi(
            "Costo Total Producción",
            f"${costo_total_prod:,.2f}",
            color_class="kpi-value-warning",
        )
    with col5:
        draw_kpi(
            "Margen Contribución",
            f"{pct_margen:.1f}%",
            sub=f"+${contribucion_marg:,.0f}",
        )

    # Fila 2 de KPIs
    col6, col7, col8, col9 = st.columns(4)
    with col6:
        draw_kpi(
            "Precio Prom. Real Unit.",
            f"${precio_prom_unit:,.2f}",
            color_class="kpi-value-neutral",
        )
    with col7:
        draw_kpi("Facturación Lista", f"${fact_lista:,.2f}")
    with col8:
        draw_kpi(
            "Descuento Comercial",
            f"${descuento_comercial:,.2f}",
            color_class="kpi-value-warning",
        )
    with col9:
        draw_kpi(
            "Insumos en Receta",
            f"{len(receta_prod)} Insumos",
            color_class="kpi-value-neutral",
        )

    st.divider()

    # ---------------------------------------------------------
    # GRAFICOS
    # ---------------------------------------------------------
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📊 Ranking de Insumos por Costo ($)")
        if not receta_prod.empty:
            df_sorted = receta_prod.sort_values(
                "Costo Insumo ($)", ascending=True
            )
            fig_bar = px.bar(
                df_sorted,
                x="Costo Insumo ($)",
                y="Descripción",
                orientation="h",
                text_auto=".2f",
                template="plotly_dark",
                color="Costo Insumo ($)",
                color_continuous_scale="Viridis",
            )
            fig_bar.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                height=380,
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_g2:
        st.subheader("🍩 Distribución Percentual del Costo")
        if not receta_prod.empty and costo_unitario > 0:
            fig_pie = px.pie(
                receta_prod,
                names="Descripción",
                values="Costo Insumo ($)",
                hole=0.5,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_pie.update_traces(
                textposition="inside", textinfo="percent+label"
            )
            fig_pie.update_layout(
                showlegend=False,  # Ocultamos leyenda lateral gigante para evitar romper el espacio
                margin=dict(l=10, r=10, t=30, b=10),
                height=380,
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # TABLA Y SANKEY
    # ---------------------------------------------------------
    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        st.subheader("📋 Desglose de Receta (BOM)")
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
        st.subheader("🔀 Flujo de Insumos al Costo Total")
        if not receta_prod.empty:
            sources = list(range(len(receta_prod)))
            targets = [len(receta_prod)] * len(receta_prod)
            values = receta_prod["Costo Insumo ($)"].tolist()
            labels = receta_prod["Descripción"].tolist() + [nombre_art]

            fig_sankey = go.Figure(
                data=[
                    go.Sankey(
                        node=dict(
                            pad=15,
                            thickness=15,
                            line=dict(color="#0E1117", width=0.5),
                            label=labels,
                            color="#29B6F6",
                        ),
                        link=dict(
                            source=sources,
                            target=targets,
                            value=values,
                            color="rgba(0, 230, 118, 0.35)",
                        ),
                    )
                ]
            )
            fig_sankey.update_layout(
                template="plotly_dark",
                margin=dict(l=5, r=5, t=10, b=10),
                height=340,
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
            )
            st.plotly_chart(fig_sankey, use_container_width=True)

else:
    # ---------------------------------------------------------
    # VISTA GENERAL DE LA COMPAÑÍA
    # ---------------------------------------------------------
    st.title("🌐 Visión General Consolidada")
    st.caption("Consolidado general de ventas, márgenes e insumos clave")

    # Cálculos globales
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

    # KPIs Consolidados
    gk1, gk2, gk3, gk4 = st.columns(4)
    with gk1:
        draw_kpi("Facturación Neta Global", f"${tot_fact_neta:,.2f}")
    with gk2:
        draw_kpi(
            "Costo Total Insumos",
            f"${tot_costo_ventas:,.2f}",
            color_class="kpi-value-warning",
        )
    with gk3:
        draw_kpi(
            "Margen Bruto Global",
            f"${tot_margen:,.2f}",
            sub=f"{pct_margen_global:.1f}% Margen",
        )
    with gk4:
        draw_kpi(
            "Volumen Total Vendido",
            f"{tot_volumen:,.0f} u.",
            color_class="kpi-value-neutral",
        )

    st.divider()

    col_g_left, col_g_right = st.columns(2)

    with col_g_left:
        st.subheader("🌳 Treemap: Insumos de Mayor Impacto Global")
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

        fig_tree = px.treemap(
            insumos_summary,
            path=["Descripción"],
            values="Gasto Total Insumo ($)",
            template="plotly_dark",
            color="Gasto Total Insumo ($)",
            color_continuous_scale="Plasma",
        )
        fig_tree.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            height=400,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    with col_g_right:
        st.subheader("🏆 Top 10 Productos por Facturación")
        top_ventas = (
            df_ventas_merged.groupby("Nombre")["Facturación Neta"]
            .sum()
            .reset_index()
            .sort_values("Facturación Neta", ascending=False)
            .head(10)
        )
        fig_top = px.bar(
            top_ventas,
            x="Facturación Neta",
            y="Nombre",
            orientation="h",
            template="plotly_dark",
            color="Facturación Neta",
            color_continuous_scale="Cividis",
        )
        fig_top.update_layout(
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,
            height=400,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
        )
        st.plotly_chart(fig_top, use_container_width=True)
