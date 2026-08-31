import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA EN MODO OSCURO
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Cost & Margin Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para reforzar Dark Mode
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        div[data-testid="metric-container"] {
            background-color: #1E222D;
            border: 1px solid #2B313E;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="metric-container"] label {
            color: #A0AAB8 !important;
            font-size: 0.9rem !important;
            font-weight: 600;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: #00E676 !important;
            font-size: 1.6rem !important;
            font-weight: 700;
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

    # Limpieza de valores nulos
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

# ---------------------------------------------------------
# NAVEGACIÓN Y FILTROS LATERALES
# ---------------------------------------------------------
st.sidebar.image(
    "https://img.icons8.com/isometric/100/analytics.png", width=70
)
st.sidebar.title("Control Center")
vista = st.sidebar.radio(
    "Seleccione Vista:",
    ["🔎 Análisis por Producto", "🌐 Visión General de Compañía"],
)

st.sidebar.divider()

if vista == "🔎 Análisis por Producto":
    st.sidebar.header("Filtros de Artículo")

    # Obtener lista única de productos con descripción
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
        "Buscar Artículo:", list(opciones_dict.keys())
    )
    cod_art = opciones_dict[item_seleccionado]
    nombre_art = item_seleccionado.split(" - ")[1]

    # --- CÁLCULOS ESPECÍFICOS DEL PRODUCTO ---
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
    # HEADER Y KPIS PRINCIPALES DEL PRODUCTO
    # ---------------------------------------------------------
    st.title(f"📦 {nombre_art}")
    st.caption(
        f"Código de Venta: **{cod_art}** | Análisis de Costos de Estructura e Insumos"
    )

    st.subheader("🚀 Indicadores Clave de Rendimiento (KPIs)")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    kpi1.metric("Costo Teórico Unitario", f"${costo_unitario:,.2f}")
    kpi2.metric("Volumen Vendido", f"{volumen_unid:,.0f} u.")
    kpi3.metric("Facturación Neta Total", f"${fact_neta:,.2f}")
    kpi4.metric("Costo Total Producción", f"${costo_total_prod:,.2f}")
    kpi5.metric(
        "Margen Contribución",
        f"{pct_margen:.1f}%",
        delta=f"${contribucion_marg:,.0f}",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    kpi6, kpi7, kpi8, kpi9 = st.columns(4)
    kpi6.metric("Precio Prom. Real Unit.", f"${precio_prom_unit:,.2f}")
    kpi7.metric("Facturación Lista", f"${fact_lista:,.2f}")
    kpi8.metric("Descuento Comercial", f"${descuento_comercial:,.2f}")
    kpi9.metric("Cantidad Insumos BOM", f"{len(receta_prod)}")

    st.divider()

    # ---------------------------------------------------------
    # VISUALIZACIONES AVANZADAS
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
                color_continuous_scale="Blues",
            )
            fig_bar.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=30, b=10),
                height=380,
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
                color_discrete_sequence=px.colors.qualitative.Dark24,
            )
            fig_pie.update_traces(
                textposition="inside", textinfo="percent+label"
            )
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=30, b=10), height=380
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # TABLA DE DETALLE Y DIAGRAMA DE FLUJO SANKEY
    # ---------------------------------------------------------
    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        st.subheader("📝 Desglose de Receta (Bill of Materials)")
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
            "Descripción Insumo",
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
            height=320,
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
                            line=dict(color="white", width=0.5),
                            label=labels,
                            color="#29B6F6",
                        ),
                        link=dict(
                            source=sources,
                            target=targets,
                            value=values,
                            color="rgba(0, 230, 118, 0.3)",
                        ),
                    )
                ]
            )
            fig_sankey.update_layout(
                template="plotly_dark",
                margin=dict(l=5, r=5, t=10, b=10),
                height=320,
            )
            st.plotly_chart(fig_sankey, use_container_width=True)


else:
    # ---------------------------------------------------------
    # VISTA GENERAL DE LA COMPAÑÍA
    # ---------------------------------------------------------
    st.title("🌐 Visión General de la Compañía")
    st.caption("Consolidado global de ventas, costos e insumos")

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
    gkpi1, gkpi2, gkpi3, gkpi4 = st.columns(4)
    gkpi1.metric("Facturación Neta Global", f"${tot_fact_neta:,.2f}")
    gkpi2.metric("Costo Total de Insumos", f"${tot_costo_ventas:,.2f}")
    gkpi3.metric(
        "Margen Bruto Global",
        f"${tot_margen:,.2f}",
        delta=f"{pct_margen_global:.1f}%",
    )
    gkpi4.metric("Volumen Total Vendido", f"{tot_volumen:,.0f} u.")

    st.divider()

    col_g_left, col_g_right = st.columns(2)

    with col_g_left:
        st.subheader("🌳 Treemap: Insumos de Mayor Impacto Económico")
        # Insumo consumido a nivel global
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
            color_continuous_scale="Viridis",
        )
        fig_tree.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=400)
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
            color_continuous_scale="Tealgrn",
        )
        fig_top.update_layout(
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,
            height=400,
        )
        st.plotly_chart(fig_top, use_container_width=True)
