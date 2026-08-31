import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Tablero de Costos y Recetas",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def cargar_datos():
    # Carga de archivos directamente del directorio
    df_ventas = pd.read_excel("VENTAS.xlsx", header=7)
    df_receta = pd.read_excel("RECETA.xlsx")
    df_precios = pd.read_excel("PRECIOS.xlsx")
    df_teoricos = pd.read_excel("TEORICOS.xlsx", header=6)

    # Normalización de columnas clave de relación
    df_ventas.rename(columns={"ART": "Cod. Venta"}, inplace=True)

    df_ventas["Cod. Venta"] = pd.to_numeric(
        df_ventas["Cod. Venta"], errors="coerce"
    )
    df_receta["Cod. Venta"] = pd.to_numeric(
        df_receta["Cod. Venta"], errors="coerce"
    )
    df_teoricos["Cod. Venta"] = pd.to_numeric(
        df_teoricos["Cod. Venta"], errors="coerce"
    )

    df_receta["Código Insumo"] = pd.to_numeric(
        df_receta["Código Insumo"], errors="coerce"
    )
    df_precios["Código Insumo"] = pd.to_numeric(
        df_precios["Código Insumo"], errors="coerce"
    )

    return df_ventas, df_receta, df_precios, df_teoricos


df_ventas, df_receta, df_precios, df_teoricos = cargar_datos()

st.title("📊 Composición de Costos, Receta e Insumos")

# --- FILTROS SIDEBAR ---
st.sidebar.header("Selección de Artículo")
articulos = (
    df_receta[["Cod. Venta", "Artículo"]]
    .dropna()
    .drop_duplicates()
    .sort_values("Artículo")
)
lista_opciones = [
    f"{int(r['Cod. Venta'])} - {r['Artículo']}"
    for _, r in articulos.iterrows()
]

opcion = st.sidebar.selectbox("Seleccione un Artículo:", lista_opciones)
cod_seleccionado = int(opcion.split(" - ")[0])

# --- CRUCE DE DATOS ---
receta_filtrada = df_receta[df_receta["Cod. Venta"] == cod_seleccionado]
receta_precios = pd.merge(
    receta_filtrada, df_precios, on="Código Insumo", how="left"
)

receta_precios["Costo Total Insumo ($)"] = (
    receta_precios["Cant. Teorica"] * receta_precios["Precio Compra"]
)
costo_teorico_unitario = receta_precios["Costo Total Insumo ($)"].sum()

ventas_filtradas = df_ventas[df_ventas["Cod. Venta"] == cod_seleccionado]
unidades_vendidas = (
    ventas_filtradas["Físicos"].sum()
    if "Físicos" in ventas_filtradas.columns
    else 0
)
facturacion = (
    ventas_filtradas["Facturación Neta"].sum()
    if "Facturación Neta" in ventas_filtradas.columns
    else 0
)

# --- TARJETAS DE METRICAS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Código Artículo", cod_seleccionado)
c2.metric("Costo Teórico Receta", f"${costo_teorico_unitario:,.2f}")
c3.metric("Unidades Vendidas", f"{unidades_vendidas:,.0f}")
c4.metric("Facturación Neta", f"${facturacion:,.2f}")

st.divider()

# --- DETALLE DE RECETA Y COSTOS ---
col_tabla, col_grafico = st.columns([3, 2])

with col_tabla:
    st.subheader("📋 Insumos y Precios de la Receta")
    tabla_mostrar = receta_precios[
        [
            "Código Insumo",
            "Descripción",
            "Cant. Teorica",
            "Precio Compra",
            "Costo Total Insumo ($)",
        ]
    ].copy()
    tabla_mostrar.columns = [
        "Cód. Insumo",
        "Insumo",
        "Cant. Teórica",
        "Precio Compra Unit.",
        "Costo Total ($)",
    ]
    st.dataframe(tabla_mostrar, use_container_width=True)

with col_grafico:
    st.subheader("🍰 Participación en el Costo")
    if not receta_precios.empty and costo_teorico_unitario > 0:
        fig_pie = px.pie(
            receta_precios,
            names="Descripción",
            values="Costo Total Insumo ($)",
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# --- FLUJO SANKEY ---
st.divider()
st.subheader("🔀 Diagrama de Flujo de Costos (Insumos -> Artículo)")

if not receta_precios.empty:
    fuentes = list(range(len(receta_precios)))
    destinos = [len(receta_precios)] * len(receta_precios)
    valores = receta_precios["Costo Total Insumo ($)"].tolist()
    etiquetas = receta_precios["Descripción"].tolist() + [
        opcion.split(" - ")[1]
    ]

    fig_sankey = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=etiquetas,
                ),
                link=dict(source=fuentes, target=destinos, value=valores),
            )
        ]
    )
    st.plotly_chart(fig_sankey, use_container_width=True)
