import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA RESPONSIVA Y MOBILE-FIRST
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Mobile Dashboard",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",  # En móviles arranca colapsado para ganar espacio
)

# Estilos CSS Mobile-First
st.markdown(
    """
    <style>
        /* Fondo general */
        .stApp {
            background-color: #0E1117;
            color: #E0E6ED;
        }
        
        /* Ajuste de contenedor principal para móviles */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }

        /* Tarjeta KPI en Mobile */
        .kpi-card-mobile {
            background: linear-gradient(135deg, #1E222D 0%, #171A21 100%);
            border: 1px solid #2A303C;
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            width: 100%;
        }
        .kpi-title-mobile {
            color: #8C9BAE;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            margin-bottom: 4px;
        }
        .kpi-value-mobile {
            color: #00E676;
            font-size: 1.3rem;
            font-weight: 700;
            line-height: 1.2;
            word-break: break-all;
        }
        .kpi-sub-mobile {
            color: #4CAF50;
            font-size: 0.75rem;
            margin-top: 3px;
            font-weight: 500;
        }
        .kpi-neutral { color: #29B6F6 !important; }
        .kpi-warning { color: #FFB74D !important; }

        /* Ajustes Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #131722;
            border-right: 1px solid #2A303C;
        }

        /* Tablas adaptables con scroll horizontal */
        [data-testid="stDataFrame"] {
            background-color: #1E222D;
            border-radius: 8px;
            padding: 4px;
            overflow-x: auto;
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


# Componente HTML para Tarjetas KPI en Móvil
def draw_kpi_mobile(title, value, sub="", color_class=""):
    val_class = f"kpi-value-mobile {color_class}".strip()
    sub_html = f'<div class="kpi-sub-mobile">{sub}</div>' if sub else ""
    html = f"""
    <div class="kpi-card-mobile">
        <div class="kpi-title-mobile">{title}</div>
        <div class="{val_class}">{value}</div>
        {sub_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# Función auxiliar para abreviar textos largos en mobile
def truncate_text(text, max_len=22):
    text = str(text)
    return text[:max_len] + "..." if len(text) > max_len else text


# Configuración del menú desplegable de Plotly para celulares
plotly_config = {
    "responsive": True,
    "displayModeBar": False,  # Oculta botones molestos sobre el gráfico en celulares
}

# ---------------------------------------------------------
# SIDEBAR / NAVEGACIÓN
# ---------------------------------------------------------
st.sidebar.title("⚡ Menu Principal")
vista = st.sidebar.radio(
    "Modo de Vista:",
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
    # ENCABEZADO Y KPIS
    # ---------------------------------------------------------
    st.subheader(f"📦 {nombre_art}")
    st.caption(f"Cód. Venta: **{cod_art}**")

    # Layout de KPIs adaptable (2 por fila en móvil)
    k1, k2 = st.columns(2)
    with k1:
        draw_kpi_mobile(
            "Costo Teórico Unit.",
            f"${costo_unitario:,.2f}",
            color_class="kpi-warning",
        )
    with k2:
        draw_kpi_mobile("Volumen Vendido", f"{volumen_unid:,.0f} u.")

    k3, k4 = st.columns(2)
    with k3:
        draw_kpi_mobile("Facturación Neta", f"${fact_neta:,.2f}")
    with k4:
        draw_kpi_mobile(
            "Costo Producción",
            f"${costo_total_prod:,.2f}",
            color_class="kpi-warning",
        )

    k5, k6 = st.columns(2)
    with k5:
        draw_kpi_mobile(
            "Margen Contribución",
            f"{pct_margen:.1f}%",
            sub=f"+${contribucion_marg:,.0f}",
        )
    with k6:
        draw_kpi_mobile(
            "Precio Prom. Real",
            f"${precio_prom_unit:,.2f}",
            color_class="kpi-neutral",
        )

    st.divider()

    # ---------------------------------------------------------
    # GRÁFICOS ADAPTABLES A PANTALLA TÁCTIL
    # ---------------------------------------------------------
    st.markdown("### 📊 Composición de Costos")

    if not receta_prod.empty:
        df_sorted = receta_prod.sort_values(
            "Costo Insumo ($)", ascending=True
        ).copy()
        df_sorted["Insumo_Corto"] = df_sorted["Descripción"].apply(
            lambda x: truncate_text(x, 22)
        )

        fig_bar = px.bar(
            df_sorted,
            x="Costo Insumo ($)",
            y="Insumo_Corto",
            orientation="h",
            text_auto=".2f",
            template="plotly_dark",
            color="Costo Insumo ($)",
            color_continuous_scale="Viridis",
            title="Ranking de Insumos por Costo ($)",
        )
        fig_bar.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=35, b=10),
            height=320,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(
            fig_bar, use_container_width=True, config=plotly_config
        )

    st.divider()

    if not receta_prod.empty and costo_unitario > 0:
        receta_prod_copy = receta_prod.copy()
        receta_prod_copy["Insumo_Corto"] = receta_prod_copy[
            "Descripción"
        ].apply(lambda x: truncate_text(x, 20))

        fig_pie = px.pie(
            receta_prod_copy,
            names="Insumo_Corto",
            values="Costo Insumo ($)",
            hole=0.45,
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Bold,
            title="Distribución % Insumos",
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=35, b=10),
            height=320,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
        )
        st.plotly_chart(fig_pie, use_container_width=True, config=plotly_config)

    st.divider()

    # ---------------------------------------------------------
    # TABLA DE DETALLE RESPONSIVA
    # ---------------------------------------------------------
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
        "Cód.",
        "Insumo",
        "Cant. Teórica",
        "Precio Unit. ($)",
        "Costo ($)",
        "% Part.",
    ]

    st.dataframe(
        tabla_out.style.format(
            {
                "Cant. Teórica": "{:,.4f}",
                "Precio Unit. ($)": "${:,.2f}",
                "Costo ($)": "${:,.2f}",
                "% Part.": "{:.1f}%",
            }
        ),
        use_container_width=True,
        height=300,
    )

    st.divider()

    # ---------------------------------------------------------
    # SANKEY RESPONSIVO
    # ---------------------------------------------------------
    st.markdown("### 🔀 Flujo de Insumos")
    if not receta_prod.empty:
        sources = list(range(len(receta_prod)))
        targets = [len(receta_prod)] * len(receta_prod)
        values = receta_prod["Costo Insumo ($)"].tolist()
        labels = [
            truncate_text(d, 18) for d in receta_prod["Descripción"].tolist()
        ] + [truncate_text(nombre_art, 18)]

        fig_sankey = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=10,
                        thickness=12,
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
            height=300,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
        )
        st.plotly_chart(
            fig_sankey, use_container_width=True, config=plotly_config
        )

else:
    # ---------------------------------------------------------
    # VISTA GENERAL DE LA COMPAÑÍA (MOBILE)
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

    # KPIs Consolidados
    gk1, gk2 = st.columns(2)
    with gk1:
        draw_kpi_mobile("Facturación Global", f"${tot_fact_neta:,.2f}")
    with gk2:
        draw_kpi_mobile(
            "Costo Insumos",
            f"${tot_costo_ventas:,.2f}",
            color_class="kpi-warning",
        )

    gk3, gk4 = st.columns(2)
    with gk3:
        draw_kpi_mobile(
            "Margen Bruto",
            f"${tot_margen:,.2f}",
            sub=f"{pct_margen_global:.1f}% Margen",
        )
    with gk4:
        draw_kpi_mobile(
            "Volumen Total", f"{tot_volumen:,.0f} u.", color_class="kpi-neutral"
        )

    st.divider()

    # Treemap Insumos Global
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
        lambda x: truncate_text(x, 22)
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
        margin=dict(l=5, r=5, t=25, b=5),
        height=350,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
    )
    st.plotly_chart(fig_tree, use_container_width=True, config=plotly_config)

    st.divider()

    # Top Productos
    st.markdown("### 🏆 Top 10 Productos por Facturación")
    top_ventas = (
        df_ventas_merged.groupby("Nombre")["Facturación Neta"]
        .sum()
        .reset_index()
        .sort_values("Facturación Neta", ascending=False)
        .head(10)
    )
    top_ventas["Nombre_Corto"] = top_ventas["Nombre"].apply(
        lambda x: truncate_text(x, 20)
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
        height=350,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        xaxis_title="",
        yaxis_title="",
    )
    st.plotly_chart(fig_top, use_container_width=True, config=plotly_config)
