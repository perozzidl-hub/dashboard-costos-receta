import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA RESPONSIVA Y DARK MODE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Dashboard - Costos & Ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# ESTILOS CSS AVANZADOS (DARK MODE & TABLAS ELEGANTES)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
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

        [data-testid="stDataFrame"] {
            background-color: #1E293B !important;
            border-radius: 8px;
            border: 1px solid #334155;
            padding: 6px;
        }

        section[data-testid="stSidebar"] {
            background-color: #0F172A;
            border-right: 1px solid #1E293B;
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

    # Renombrar código de producto si aplica
    df_ventas.rename(columns={"ART": "Cod. Venta"}, inplace=True)

    # Extraer formato de fecha/mes
    if "FECHA" in df_ventas.columns:
        df_ventas["FECHA"] = pd.to_datetime(df_ventas["FECHA"], errors="coerce")
        df_ventas["Mes_Venta"] = df_ventas["FECHA"].dt.strftime("%Y-%m")
    else:
        df_ventas["Mes_Venta"] = "Sin Fecha"

    # Conversión numérica
    for df in [df_ventas, df_receta]:
        df["Cod. Venta"] = pd.to_numeric(df["Cod. Venta"], errors="coerce")

    for df in [df_receta, df_precios]:
        df["Código Insumo"] = pd.to_numeric(
            df["Código Insumo"], errors="coerce"
        )

    df_ventas = df_ventas.dropna(subset=["Cod. Venta"])
    df_receta = df_receta.dropna(subset=["Cod. Venta", "Código Insumo"])

    # Asegurar columna TOTAL INSUMOS
    if "TOTAL INSUMOS" not in df_ventas.columns:
        df_ventas["TOTAL INSUMOS"] = 0.0
    else:
        df_ventas["TOTAL INSUMOS"] = pd.to_numeric(
            df_ventas["TOTAL INSUMOS"], errors="coerce"
        ).fillna(0.0)

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


def truncate_text(text, max_len=26):
    text = str(text)
    return text[:max_len] + "..." if len(text) > max_len else text


plotly_config = {"responsive": True, "displayModeBar": False}

# ---------------------------------------------------------
# SIDEBAR / FILTROS DE MES Y LOCACIÓN-SAP
# ---------------------------------------------------------
st.sidebar.title("⚡ Control Center")
vista = st.sidebar.radio(
    "Seleccionar Vista:",
    ["🔎 Análisis por Producto", "🌐 Visión General de Compañía"],
)

st.sidebar.divider()
st.sidebar.header("🗓️ Filtros Globales")

# 1. Filtro Mes
meses_disponibles = sorted(
    list(set(df_ventas["Mes_Venta"].dropna().unique()))
)
opciones_mes = ["Todos los Meses"] + [m for m in meses_disponibles if m != ""]
mes_seleccionado = st.sidebar.selectbox("Mes de Venta:", opciones_mes)

# 2. Filtro Locación SAP
locaciones_disponibles = sorted(
    [
        str(loc)
        for loc in df_ventas["LOCACION - SAP"].dropna().unique()
        if str(loc).strip() != ""
    ]
)
opciones_locacion = ["Todas las Locaciones"] + locaciones_disponibles
locacion_seleccionada = st.sidebar.selectbox(
    "Locación - SAP:", opciones_locacion
)

# Aplicar Filtros Globales a Ventas
df_ventas_filt = df_ventas.copy()
if mes_seleccionado != "Todos los Meses":
    df_ventas_filt = df_ventas_filt[
        df_ventas_filt["Mes_Venta"] == mes_seleccionado
    ]

if locacion_seleccionada != "Todas las Locaciones":
    df_ventas_filt = df_ventas_filt[
        df_ventas_filt["LOCACION - SAP"] == locacion_seleccionada
    ]

st.sidebar.divider()

if vista == "🔎 Análisis por Producto":
    st.sidebar.header("📦 Seleccionar Producto")

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

    # Datos Receta Teórica por Producto
    receta_prod = receta_precios[receta_precios["Cod. Venta"] == cod_art].copy()
    costo_unitario_teorico = receta_prod["Costo Insumo ($)"].sum()

    # Ventas filtradas del Producto
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

    # COSTO DE INSUMOS DIRECTO DE LA COLUMNA DE VENTAS EXCEL
    costo_insumos_excel = ventas_prod["TOTAL INSUMOS"].sum()

    contribucion_marg = fact_neta - costo_insumos_excel
    pct_margen = (
        (contribucion_marg / fact_neta * 100) if fact_neta > 0 else 0.0
    )
    descuento_comercial = fact_lista - fact_neta
    precio_prom_unit = (fact_neta / volumen_unid) if volumen_unid > 0 else 0.0

    # ---------------------------------------------------------
    # ENCABEZADO Y KPIS CORREGIDOS
    # ---------------------------------------------------------
    st.title(f"📦 {nombre_art}")

    st.markdown(
        f"""
        <div class="month-banner">
            📅 Período: <strong>{mes_seleccionado}</strong> | 📍 Locación: <strong>{locacion_seleccionada}</strong> | Código SAP: <strong>{cod_art}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        draw_kpi("Facturación Neta", f"${fact_neta:,.2f}")
    with col2:
        # COSTO DE INSUMOS COINCIDENTE CON EXCEL DE VENTAS
        draw_kpi(
            "Costo de Insumos",
            f"${costo_insumos_excel:,.2f}",
            color_class="kpi-warning",
        )
    with col3:
        draw_kpi(
            "Margen Contribución",
            f"{pct_margen:.1f}%",
            sub=f"+${contribucion_marg:,.0f}",
        )
    with col4:
        draw_kpi(
            "Volumen Vendido",
            f"{volumen_unid:,.0f} u.",
            color_class="kpi-neutral",
        )
    with col5:
        draw_kpi(
            "Costo Teórico Unit.",
            f"${costo_unitario_teorico:,.2f}",
            color_class="kpi-warning",
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
    # GRÁFICOS CON SUMATORIAS E IMPORTES TOTALES
    # ---------------------------------------------------------
    st.markdown("### 📊 Composición de Insumos e Importes Totales")
    col_g1, col_g2 = st.columns([3, 2])

    # Sumatoria total del gráfico actual
    total_costo_grafico = receta_prod["Costo Insumo ($)"].sum()

    with col_g1:
        if not receta_prod.empty:
            df_sorted = receta_prod.sort_values(
                "Costo Insumo ($)", ascending=True
            ).copy()
            df_sorted["Insumo_Label"] = df_sorted["Descripción"].apply(
                lambda x: truncate_text(x, 26)
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
                title=f"Desglose por Insumo (Total Receta Unit.: ${total_costo_grafico:,.2f})",
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
        if not receta_prod.empty and total_costo_grafico > 0:
            receta_prod_copy = receta_prod.copy()
            receta_prod_copy["Insumo_Label"] = receta_prod_copy[
                "Descripción"
            ].apply(lambda x: truncate_text(x, 18))

            fig_pie = px.pie(
                receta_prod_copy,
                names="Insumo_Label",
                values="Costo Insumo ($)",
                hole=0.48,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold,
                title="Distribución Percentual de Costos",
            )
            fig_pie.update_traces(
                textposition="inside", textinfo="percent+label"
            )
            # Anotación central con el importe total
            fig_pie.add_annotation(
                text=f"<b>Total</b><br>${total_costo_grafico:,.2f}",
                x=0.5,
                y=0.5,
                font_size=13,
                showarrow=False,
                font_color="#38BDF8",
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
    # TABLA DESGLOSE (BOM) CON FILA DE SUMATORIA TOTAL
    # ---------------------------------------------------------
    col_t1, col_t2 = st.columns([3, 2])

    with col_t1:
        st.markdown("### 📋 Desglose de Receta (BOM) con Totales")
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
            tabla_out["Costo Insumo ($)"] / total_costo_grafico * 100
            if total_costo_grafico > 0
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

        # Convertir a texto formateado y agregar Fila TOTAL
        tabla_out_formatted = tabla_out.copy()
        tabla_out_formatted["Cant. Teórica"] = tabla_out_formatted[
            "Cant. Teórica"
        ].apply(lambda x: f"{x:,.4f}")
        tabla_out_formatted["Precio Unit. ($)"] = tabla_out_formatted[
            "Precio Unit. ($)"
        ].apply(lambda x: f"${x:,.2f}")
        tabla_out_formatted["Costo ($)"] = tabla_out_formatted["Costo ($)"].apply(
            lambda x: f"${x:,.2f}"
        )
        tabla_out_formatted["% Participación"] = tabla_out_formatted[
            "% Participación"
        ].apply(lambda x: f"{x:.1f}%")

        # Fila Total
        fila_total = pd.DataFrame(
            [
                {
                    "Cód. Insumo": "TOTAL",
                    "Insumo": "SUMATORIA TOTAL RECURSOS",
                    "Cant. Teórica": "-",
                    "Precio Unit. ($)": "-",
                    "Costo ($)": f"${total_costo_grafico:,.2f}",
                    "% Participación": "100.0%",
                }
            ]
        )

        tabla_final = pd.concat(
            [tabla_out_formatted, fila_total], ignore_index=True
        )
        st.dataframe(tabla_final, use_container_width=True, height=340)

    with col_t2:
        st.markdown("### 📊 Contribución Acumulada")
        if not receta_prod.empty:
            df_flujo = receta_prod.sort_values(
                "Costo Insumo ($)", ascending=True
            ).copy()
            df_flujo["Insumo_Corto"] = df_flujo["Descripción"].apply(
                lambda x: truncate_text(x, 22)
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
                title=f"Importe Total Generado: ${total_costo_grafico:,.2f}",
            )
            fig_flujo.update_traces(
                texttemplate="$%{x:,.2f}", textposition="outside"
            )
            fig_flujo.update_layout(
                showlegend=False,
                margin=dict(l=10, r=40, t=30, b=10),
                height=340,
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#0B0E14",
                xaxis_title="",
                yaxis_title="",
                coloraxis_showscale=False,
            )
            st.plotly_chart(
                fig_flujo, use_container_width=True, config=plotly_config
            )

else:
    # ---------------------------------------------------------
    # VISTA GENERAL CON SENSITIVIDAD DE LOCACIÓN - SAP
    # ---------------------------------------------------------
    st.title("🌐 Visión General Consolidada de Compañía")

    st.markdown(
        f"""
        <div class="month-banner">
            📅 Período: <strong>{mes_seleccionado}</strong> | 📍 Locación SAP: <strong>{locacion_seleccionada}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tot_fact_neta = df_ventas_filt["Facturación Neta"].sum()
    # COSTO DE INSUMOS DIRECTO DE COLUMNA TOTAL INSUMOS
    tot_costo_insumos = df_ventas_filt["TOTAL INSUMOS"].sum()
    tot_margen = tot_fact_neta - tot_costo_insumos
    tot_volumen = df_ventas_filt["Físicos"].sum()
    pct_margen_global = (
        (tot_margen / tot_fact_neta * 100) if tot_fact_neta > 0 else 0
    )

    gk1, gk2, gk3, gk4 = st.columns(4)
    with gk1:
        draw_kpi("Facturación Global", f"${tot_fact_neta:,.2f}")
    with gk2:
        draw_kpi(
            "Costo de Insumos",
            f"${tot_costo_insumos:,.2f}",
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
        st.markdown("### 📍 Ventas y Costo de Insumos por Locación SAP")
        loc_summary = (
            df_ventas_filt.groupby("LOCACION - SAP")[
                ["Facturación Neta", "TOTAL INSUMOS"]
            ]
            .sum()
            .reset_index()
        )
        loc_summary.rename(
            columns={"TOTAL INSUMOS": "Costo de Insumos"}, inplace=True
        )

        fig_loc = px.bar(
            loc_summary,
            x="LOCACION - SAP",
            y=["Facturación Neta", "Costo de Insumos"],
            barmode="group",
            template="plotly_dark",
            color_discrete_map={
                "Facturación Neta": "#4ADE80",
                "Costo de Insumos": "#FBBF24",
            },
            title=f"Comparativo Facturación vs Insumos (Total: ${tot_fact_neta:,.2f})",
        )
        fig_loc.update_layout(
            margin=dict(l=10, r=10, t=35, b=10),
            height=380,
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#0B0E14",
            xaxis_title="",
            yaxis_title="",
            legend_title="",
        )
        st.plotly_chart(
            fig_loc, use_container_width=True, config=plotly_config
        )

    with col_g_right:
        st.markdown("### 🏆 Top 10 Productos por Facturación")
        top_ventas = (
            df_ventas_filt.groupby("Nombre")["Facturación Neta"]
            .sum()
            .reset_index()
            .sort_values("Facturación Neta", ascending=False)
            .head(10)
        )
        top_ventas["Nombre_Corto"] = top_ventas["Nombre"].apply(
            lambda x: truncate_text(x, 22)
        )

        tot_top10 = top_ventas["Facturación Neta"].sum()

        fig_top = px.bar(
            top_ventas,
            x="Facturación Neta",
            y="Nombre_Corto",
            orientation="h",
            template="plotly_dark",
            color="Facturación Neta",
            color_continuous_scale="Cividis",
            title=f"Suma Top 10: ${tot_top10:,.2f}",
        )
        fig_top.update_traces(
            texttemplate="$%{x:,.2f}", textposition="outside"
        )
        fig_top.update_layout(
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,
            height=380,
            margin=dict(l=10, r=40, t=35, b=10),
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#0B0E14",
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(
            fig_top, use_container_width=True, config=plotly_config
        )
