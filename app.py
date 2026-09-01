import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# ESTILOS CSS AVANZADOS (TABLAS CLARAS Y ALTO CONTRASTE)
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

        /* BADGES DE TIPO PROD */
        .type-badge {
            background-color: #38BDF8;
            color: #0F172A;
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 0.82rem;
            margin-left: 10px;
        }

        /* SIDEBAR ALTO CONTRASTE */
        section[data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid #1E293B;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {
            color: #F8FAFC !important;
            font-weight: 600 !important;
        }

        section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
            background-color: #1E293B !important;
            color: #FFFFFF !important;
            border: 1px solid #475569 !important;
            border-radius: 8px;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label span {
            color: #F1F5F9 !important;
            font-size: 0.95rem !important;
        }

        /* TARJETAS DE KPIS */
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

        /* ESTILO LEGIBLE Y VISIBLE PARA TABLAS ST.TABLE */
        .stTable {
            background-color: #1E293B !important;
            border-radius: 8px;
            border: 1px solid #334155 !important;
        }
        .stTable table {
            color: #FFFFFF !important;
            background-color: #1E293B !important;
        }
        .stTable th {
            background-color: #0F172A !important;
            color: #38BDF8 !important;
            font-size: 0.9rem !important;
            border-bottom: 2px solid #334155 !important;
        }
        .stTable td {
            color: #F8FAFC !important;
            border-bottom: 1px solid #334155 !important;
            font-size: 0.88rem !important;
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
    try:
        df_ventas = pd.read_excel("VENTAS.xlsx", header=7)
        df_receta = pd.read_excel("RECETA.xlsx")
        df_precios = pd.read_excel("PRECIOS.xlsx")
    except Exception as e:
        st.error(f"Error al cargar los archivos Excel: {e}")
        st.stop()

    df_ventas.rename(columns={"ART": "Cod. Venta"}, inplace=True)

    if "FECHA" in df_ventas.columns:
        df_ventas["FECHA"] = pd.to_datetime(df_ventas["FECHA"], errors="coerce")
        df_ventas["Mes_Venta"] = df_ventas["FECHA"].dt.strftime("%Y-%m").fillna("Sin Fecha")
    else:
        df_ventas["Mes_Venta"] = "Sin Fecha"

    # Detección y normalización del tipo de producto (Propio / Reventa)
    col_tipo = None
    for col in df_ventas.columns:
        if any(k in str(col).lower() for k in ["tipo", "origen", "propio", "reventa", "clasif"]):
            col_tipo = col
            break

    if col_tipo:
        df_ventas["Tipo_Producto"] = df_ventas[col_tipo].astype(str).str.strip().str.upper()
    else:
        df_ventas["Tipo_Producto"] = "P"

    # Homogeneización estricta de tipos numéricos
    for df in [df_ventas, df_receta]:
        if "Cod. Venta" in df.columns:
            df["Cod. Venta"] = pd.to_numeric(df["Cod. Venta"], errors="coerce")

    for df in [df_receta, df_precios]:
        if "Código Insumo" in df.columns:
            df["Código Insumo"] = pd.to_numeric(df["Código Insumo"], errors="coerce")

    df_ventas = df_ventas.dropna(subset=["Cod. Venta"])

    # Conversiones numéricas de costos en VENTAS
    if "TOTAL INSUMOS" in df_ventas.columns:
        df_ventas["TOTAL INSUMOS"] = pd.to_numeric(df_ventas["TOTAL INSUMOS"], errors="coerce").fillna(0.0)
    else:
        df_ventas["TOTAL INSUMOS"] = 0.0

    if "TOTAL PRODUCTO TERCEROS" in df_ventas.columns:
        df_ventas["TOTAL PRODUCTO TERCEROS"] = pd.to_numeric(df_ventas["TOTAL PRODUCTO TERCEROS"], errors="coerce").fillna(0.0)
    else:
        df_ventas["TOTAL PRODUCTO TERCEROS"] = 0.0

    # Lógica de costo unificado en VENTAS
    df_ventas["COSTO_TOTAL_REAL"] = df_ventas.apply(
        lambda r: r["TOTAL PRODUCTO TERCEROS"] if r["Tipo_Producto"] == "R" else r["TOTAL INSUMOS"],
        axis=1,
    )

    if not df_receta.empty and "Cod. Venta" in df_receta.columns and "Código Insumo" in df_receta.columns:
        df_receta = df_receta.dropna(subset=["Cod. Venta", "Código Insumo"])
        receta_precios = pd.merge(
            df_receta,
            df_precios[["Código Insumo", "Descripción", "Precio Compra"]],
            on="Código Insumo",
            how="left",
        )
        receta_precios["Precio Compra"] = pd.to_numeric(receta_precios["Precio Compra"], errors="coerce").fillna(0.0)
        receta_precios["Cant. Teorica"] = pd.to_numeric(receta_precios["Cant. Teorica"], errors="coerce").fillna(0.0)
        receta_precios["Costo Insumo ($)"] = receta_precios["Cant. Teorica"] * receta_precios["Precio Compra"]
    else:
        receta_precios = pd.DataFrame()

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

PALETA_COLORES = [
    "#38BDF8", "#4ADE80", "#FBBF24", "#F43F5E", "#A855F7",
    "#EC4899", "#6366F1", "#14B8A6", "#F97316", "#8B5CF6",
]

# ---------------------------------------------------------
# SIDEBAR / FILTROS
# ---------------------------------------------------------
st.sidebar.title("⚡ Control Center")
vista = st.sidebar.radio(
    "Seleccionar Vista:",
    ["🔎 Análisis por Producto", "🌐 Visión General de Compañía"],
)

st.sidebar.divider()
st.sidebar.header("🗓️ Filtros Globales")

# 1. Filtro Mes
meses_disponibles = sorted([m for m in df_ventas["Mes_Venta"].dropna().unique() if str(m).strip() != ""])
opciones_mes = ["Todos los Meses"] + meses_disponibles
mes_seleccionado = st.sidebar.selectbox("Mes de Venta:", opciones_mes)

# 2. Filtro Locación
locaciones_disponibles = sorted([str(loc) for loc in df_ventas["LOCACION - SAP"].dropna().unique() if str(loc).strip() != ""])
opciones_locacion = ["Todas las Locaciones"] + locaciones_disponibles
locacion_seleccionada = st.sidebar.selectbox("Locación - SAP:", opciones_locacion)

# 3. Filtro Tipo de Producto
tipos_disponibles = sorted([str(t) for t in df_ventas["Tipo_Producto"].dropna().unique() if str(t).strip() != ""])
opciones_tipo = ["Todos los Tipos"] + tipos_disponibles
tipo_seleccionado = st.sidebar.selectbox("Tipo de Producto (Origen):", opciones_tipo)

# Aplicar Filtros Globales
df_ventas_filt = df_ventas.copy()
if mes_seleccionado != "Todos los Meses":
    df_ventas_filt = df_ventas_filt[df_ventas_filt["Mes_Venta"] == mes_seleccionado]

if locacion_seleccionada != "Todas las Locaciones":
    df_ventas_filt = df_ventas_filt[df_ventas_filt["LOCACION - SAP"] == locacion_seleccionada]

if tipo_seleccionado != "Todos los Tipos":
    df_ventas_filt = df_ventas_filt[df_ventas_filt["Tipo_Producto"] == tipo_seleccionado]

st.sidebar.divider()

if vista == "🔎 Análisis por Producto":
    st.sidebar.header("📦 Seleccionar Producto")

    col_nombre_art = "Nombre" if "Nombre" in df_ventas_filt.columns else "Artículo"
    articulos_df = df_ventas_filt[["Cod. Venta", col_nombre_art]].drop_duplicates().sort_values(col_nombre_art)

    if not articulos_df.empty:
        opciones_dict = {
            f"{int(row['Cod. Venta'])} - {row[col_nombre_art]}": int(row["Cod. Venta"])
            for _, row in articulos_df.iterrows()
        }

        item_seleccionado = st.sidebar.selectbox("Seleccionar Artículo:", list(opciones_dict.keys()))
        cod_art = opciones_dict[item_seleccionado]
        nombre_art = item_seleccionado.split(" - ", 1)[1]
    else:
        st.warning("No hay productos disponibles para los filtros seleccionados.")
        st.stop()

    ventas_prod_gen = df_ventas[df_ventas["Cod. Venta"] == cod_art]
    tipo_prod = ventas_prod_gen["Tipo_Producto"].iloc[0] if not ventas_prod_gen.empty else "P"

    ventas_prod = df_ventas_filt[df_ventas_filt["Cod. Venta"] == cod_art]

    volumen_unid = ventas_prod["Físicos"].sum() if "Físicos" in ventas_prod.columns else 0.0
    fact_lista = ventas_prod["Facturación Lista"].sum() if "Facturación Lista" in ventas_prod.columns else 0.0
    fact_neta = ventas_prod["Facturación Neta"].sum() if "Facturación Neta" in ventas_prod.columns else 0.0

    costo_total_calculado = ventas_prod["COSTO_TOTAL_REAL"].sum()
    contribucion_marg = fact_neta - costo_total_calculado
    pct_margen = (contribucion_marg / fact_neta * 100) if fact_neta > 0 else 0.0
    precio_prom_unit = (fact_neta / volumen_unid) if volumen_unid > 0 else 0.0
    costo_unitario_real = (costo_total_calculado / volumen_unid) if volumen_unid > 0 else 0.0

    # ---------------------------------------------------------
    # ENCABEZADO Y KPIS
    # ---------------------------------------------------------
    st.markdown(
        f"<h1>📦 {nombre_art} <span class='type-badge'>{tipo_prod.upper()}</span></h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="month-banner">
            📅 Período: <strong>{mes_seleccionado}</strong> | 📍 Locación: <strong>{locacion_seleccionada}</strong> | Código SAP: <strong>{cod_art}</strong> | Categoría: <strong>{tipo_prod}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🚀 Indicadores Clave Agrupados")

    etiqueta_costo = "2. Costo de Terceros" if tipo_prod == "R" else "2. Costo de Insumos"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        draw_kpi("1. Facturación Neta", f"${fact_neta:,.2f}")
    with c2:
        draw_kpi(etiqueta_costo, f"${costo_total_calculado:,.2f}", color_class="kpi-warning")
    with c3:
        draw_kpi("3. Contribución Marg. ($)", f"${contribucion_marg:,.2f}", color_class="kpi-neutral")
    with c4:
        draw_kpi("4. Contribución Marg. (%)", f"{pct_margen:.1f}%", sub="Margen Sobre Neta")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        draw_kpi("5. Facturación Unit. Prod.", f"${precio_prom_unit:,.2f}", color_class="kpi-neutral")
    with c6:
        draw_kpi("6. Costo Unitario Real", f"${costo_unitario_real:,.2f}", color_class="kpi-warning")
    with c7:
        draw_kpi("Volumen Vendido", f"{volumen_unid:,.0f} u.", color_class="kpi-neutral")
    with c8:
        draw_kpi("Tipo de Producto", f"{tipo_prod}", color_class="kpi-neutral")

    st.divider()

    # ---------------------------------------------------------
    # COMPARATIVO UNITARIO
    # ---------------------------------------------------------
    st.markdown("### ⚖️ Relación Facturación Unitaria vs. Costo Unitario")

    pct_costo_sobre_venta = (costo_unitario_real / precio_prom_unit * 100) if precio_prom_unit > 0 else 0.0

    df_unit_comp = pd.DataFrame([
        {"Concepto": "Facturación Unitaria Real", "Monto ($)": precio_prom_unit, "Tipo": "Facturación"},
        {"Concepto": "Costo Unitario Real", "Monto ($)": costo_unitario_real, "Tipo": "Costo"},
    ])

    fig_unit = px.bar(
        df_unit_comp,
        x="Monto ($)",
        y="Concepto",
        orientation="h",
        text="Monto ($)",
        template="plotly_dark",
        color="Tipo",
        color_discrete_map={"Facturación": "#4ADE80", "Costo": "#FBBF24"},
        title=f"Representación del Costo sobre Facturación Unitaria: {pct_costo_sobre_venta:.1f}%",
    )
    fig_unit.update_traces(texttemplate="$%{x:,.2f}", textposition="outside")
    fig_unit.update_layout(
        showlegend=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=10, r=60, t=35, b=10),
        height=220,
        paper_bgcolor="#0B0E14",
        plot_bgcolor="#0B0E14",
        xaxis_title="",
        yaxis_title="",
    )
    st.plotly_chart(fig_unit, config=plotly_config)

    st.divider()

    # ---------------------------------------------------------
    # COMPOSICIÓN Y TABLAS
    # ---------------------------------------------------------
    receta_prod = receta_precios[receta_precios["Cod. Venta"] == cod_art].copy() if not receta_precios.empty else pd.DataFrame()

    if tipo_prod == "P" and not receta_prod.empty:
        st.markdown("### 📊 Composición de Insumos e Importes Totales")
        total_costo_grafico = receta_prod["Costo Insumo ($)"].sum()
        col_g1, col_g2 = st.columns([3, 2])

        df_sorted_desc = receta_prod.sort_values("Costo Insumo ($)", ascending=False).copy()
        df_sorted_desc["Insumo_Label"] = df_sorted_desc["Descripción"].apply(lambda x: truncate_text(x, 26))

        insumos_unicos = df_sorted_desc["Insumo_Label"].tolist()
        mapa_colores = {insumo: PALETA_COLORES[i % len(PALETA_COLORES)] for i, insumo in enumerate(insumos_unicos)}

        with col_g1:
            fig_bar = px.bar(
                df_sorted_desc,
                x="Costo Insumo ($)",
                y="Insumo_Label",
                orientation="h",
                text="Costo Insumo ($)",
                template="plotly_dark",
                color="Insumo_Label",
                color_discrete_map=mapa_colores,
                title=f"Desglose por Insumo (Total Unit.: ${total_costo_grafico:,.2f})",
            )
            fig_bar.update_traces(texttemplate="$%{x:,.2f}", textposition="outside")
            fig_bar.update_layout(
                showlegend=False,
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=10, r=50, t=35, b=10),
                height=380,
                paper_bgcolor="#0B0E14",
                plot_bgcolor="#0B0E14",
                xaxis_title="",
                yaxis_title="",
            )
            st.plotly_chart(fig_bar, config=plotly_config)

        with col_g2:
            fig_pie = px.pie(
                df_sorted_desc,
                names="Insumo_Label",
                values="Costo Insumo ($)",
                hole=0.48,
                template="plotly_dark",
                color="Insumo_Label",
                color_discrete_map=mapa_colores,
                title="Distribución % Insumos",
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent",
                insidetextfont=dict(color="#0F172A", size=16, family="Arial Black"),
            )
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
            st.plotly_chart(fig_pie, config=plotly_config)

        st.divider()

        st.markdown("### 📋 Desglose de Receta (BOM) con Totales")

        tabla_out = receta_prod[
            ["Código Insumo", "Descripción", "Cant. Teorica", "Precio Compra", "Costo Insumo ($)"]
        ].copy()

        tabla_out["% Part."] = (
            (tabla_out["Costo Insumo ($)"] / total_costo_grafico * 100) if total_costo_grafico > 0 else 0.0
        )
        tabla_out.columns = [
            "Cód. Insumo", "Insumo", "Cant. Teórica", "Precio Unit. ($)", "Costo ($)", "% Participación",
        ]

        tabla_out_formatted = tabla_out.copy()
        tabla_out_formatted["Cant. Teórica"] = tabla_out_formatted["Cant. Teórica"].apply(lambda x: f"{x:,.4f}")
        tabla_out_formatted["Precio Unit. ($)"] = tabla_out_formatted["Precio Unit. ($)"].apply(lambda x: f"${x:,.2f}")
        tabla_out_formatted["Costo ($)"] = tabla_out_formatted["Costo ($)"].apply(lambda x: f"${x:,.2f}")
        tabla_out_formatted["% Participación"] = tabla_out_formatted["% Participación"].apply(lambda x: f"{x:.1f}%")

        fila_total = pd.DataFrame([{
            "Cód. Insumo": "TOTAL",
            "Insumo": "SUMATORIA TOTAL RECURSOS",
            "Cant. Teórica": "-",
            "Precio Unit. ($)": "-",
            "Costo ($)": f"${total_costo_grafico:,.2f}",
            "% Participación": "100.0%",
        }])

        tabla_final = pd.concat([tabla_out_formatted, fila_total], ignore_index=True)
        st.table(tabla_final)
    else:
        st.info("ℹ️ **Producto de Reventa (R)**: El costo total proviene directamente de la columna **TOTAL PRODUCTO TERCEROS** en el registro de ventas.")

else:
    # ---------------------------------------------------------
    # VISTA GENERAL DE COMPAÑÍA
    # ---------------------------------------------------------
    st.title("🌐 Visión General Consolidada de Compañía")

    st.markdown(
        f"""
        <div class="month-banner">
            📅 Período: <strong>{mes_seleccionado}</strong> | 📍 Locación SAP: <strong>{locacion_seleccionada}</strong> | Categoría Filtro: <strong>{tipo_seleccionado}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tot_fact_neta = df_ventas_filt["Facturación Neta"].sum()
    tot_costo_global = df_ventas_filt["COSTO_TOTAL_REAL"].sum()
    tot_margen = tot_fact_neta - tot_costo_global
    pct_margen_global = (tot_margen / tot_fact_neta * 100) if tot_fact_neta > 0 else 0.0

    gk1, gk2, gk3, gk4 = st.columns(4)
    with gk1:
        draw_kpi("1. Facturación Global", f"${tot_fact_neta:,.2f}")
    with gk2:
        draw_kpi("2. Costo Total (Insumos + Terceros)", f"${tot_costo_global:,.2f}", color_class="kpi-warning")
    with gk3:
        draw_kpi("3. Contribución Marg. ($)", f"${tot_margen:,.2f}", color_class="kpi-neutral")
    with gk4:
        draw_kpi("4. Contribución Marg. (%)", f"{pct_margen_global:.1f}%", sub="Margen Global")

    st.divider()

    col_g_left, col_g_right = st.columns(2)

    with col_g_left:
        st.markdown("### 📍 Ventas y Costo Total por Locación SAP")
        loc_summary = (
            df_ventas_filt.groupby("LOCACION - SAP")[["Facturación Neta", "COSTO_TOTAL_REAL"]]
            .sum()
            .reset_index()
        )
        loc_summary.rename(columns={"COSTO_TOTAL_REAL": "Costo Total"}, inplace=True)

        fig_loc = px.bar(
            loc_summary,
            x="LOCACION - SAP",
            y=["Facturación Neta", "Costo Total"],
            barmode="group",
            template="plotly_dark",
            color_discrete_map={"Facturación Neta": "#4ADE80", "Costo Total": "#FBBF24"},
            title=f"Comparativo Facturación vs Costos (Total: ${tot_fact_neta:,.2f})",
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
        st.plotly_chart(fig_loc, config=plotly_config)

    with col_g_right:
        st.markdown("### 🏆 Top 10 Productos por Facturación")
        col_nom_top = "Nombre" if "Nombre" in df_ventas_filt.columns else "Artículo"
        top_ventas = (
            df_ventas_filt.groupby(col_nom_top)["Facturación Neta"]
            .sum()
            .reset_index()
            .sort_values("Facturación Neta", ascending=False)
            .head(10)
        )
        top_ventas["Nombre_Corto"] = top_ventas[col_nom_top].apply(lambda x: truncate_text(x, 22))

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
        fig_top.update_traces(texttemplate="$%{x:,.2f}", textposition="outside")
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
        st.plotly_chart(fig_top, config=plotly_config)
