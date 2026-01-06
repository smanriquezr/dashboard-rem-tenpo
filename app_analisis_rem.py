import streamlit as st
import pandas as pd
import pandas_gbq
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Análisis Cuenta REM 2025",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .highlight-positive {
        color: #28a745;
        font-weight: bold;
    }
    .highlight-negative {
        color: #dc3545;
        font-weight: bold;
    }
    .highlight-warning {
        color: #ffc107;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Título principal
st.markdown('<p class="big-font">📊 Análisis de Cuenta Remunerada 2025</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar para opciones
st.sidebar.header("⚙️ Configuración")
usar_cache = st.sidebar.checkbox("Usar datos guardados (más rápido)", value=True)
fecha_reduccion_tasa = pd.to_datetime('2025-12-21')

# Función para cargar datos
@st.cache_data(ttl=3600)
def cargar_datos_bq():
    """Carga datos desde BigQuery"""
    project_id = "tenpo-bi-prod"

    query = """
    WITH base_revenue AS (
      SELECT fecha, user, SUM(revenue) * 1000000 AS revenue_servicios
      FROM `tenpo-bi-prod.kpitos.dataform_revenue_app`
      WHERE tipo = "revenue_servicios" AND fecha >= "2025-01-01"
      GROUP BY 1,2
    ),
    base_mau_rem AS (
      SELECT fecha, COUNT(DISTINCT user) AS mau_rem
      FROM `tenpo-bi-prod.kpitos.cohorts_cuenta_rem`
      WHERE fecha >= '2025-01-01'
      GROUP BY 1
    ),
    base_limpia AS (
      SELECT * FROM `business-data-raw.ingestor_paid_account_public.interest_payment`
      QUALIFY ROW_NUMBER() OVER(PARTITION BY date, user_id ORDER BY updated_at DESC) = 1
    ),
    diario AS (
      SELECT
        i.date AS fecha,
        SUM(i.user_balance) AS saldo_rem,
        IFNULL(m.mau_rem, 0) AS mau_rem,
        COUNT(DISTINCT i.user_id) AS dau_rem
      FROM base_limpia i
      LEFT JOIN base_revenue r ON i.user_id = r.user AND i.date = r.fecha
      LEFT JOIN base_mau_rem m ON i.date = m.fecha
      WHERE i.status = "SUCCEEDED"
        AND i.date <= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        AND i.date >= "2025-01-01"
      GROUP BY 1, 3
    )
    SELECT
      fecha,
      saldo_rem/1000000 AS saldo_rem,
      SUM(mau_rem) OVER (PARTITION BY EXTRACT(YEAR FROM fecha), EXTRACT(MONTH FROM fecha) ORDER BY fecha ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS mau_rem,
      dau_rem
    FROM diario
    ORDER BY fecha
    """

    with st.spinner('Cargando datos desde BigQuery...'):
        df = pandas_gbq.read_gbq(query, project_id=project_id, use_bqstorage_api=False)

    return df

@st.cache_data
def cargar_datos_csv():
    """Carga datos desde CSV local"""
    try:
        df = pd.read_csv('datos_saldo_detallado.csv')
        return df
    except:
        return None

# Cargar datos
if usar_cache:
    df = cargar_datos_csv()
    if df is None:
        st.warning("No se encontró archivo local. Cargando desde BigQuery...")
        df = cargar_datos_bq()
else:
    df = cargar_datos_bq()

# Procesar datos
df['fecha'] = pd.to_datetime(df['fecha'])
df = df.sort_values('fecha').reset_index(drop=True)

# Calcular métricas derivadas
df['saldo_crecimiento_absoluto_diario'] = df['saldo_rem'].diff()
df['saldo_crecimiento_pct_diario'] = df['saldo_rem'].pct_change() * 100
df['saldo_crecimiento_absoluto_semanal'] = df['saldo_rem'].diff(7)
df['saldo_crecimiento_pct_semanal'] = ((df['saldo_rem'] / df['saldo_rem'].shift(7)) - 1) * 100
df['saldo_ma7'] = df['saldo_rem'].rolling(window=7, min_periods=1).mean()
df['crecimiento_diario_ma7'] = df['saldo_crecimiento_pct_diario'].rolling(window=7, min_periods=1).mean()
df['saldo_por_mau'] = (df['saldo_rem'] / df['mau_rem']) * 1000000
df['dau_mau_ratio'] = (df['dau_rem'] / df['mau_rem']) * 100

# Dividir en períodos
df_antes = df[df['fecha'] < fecha_reduccion_tasa].copy()
df_despues = df[df['fecha'] >= fecha_reduccion_tasa].copy()

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "⚡ Velocidad de Crecimiento", "🎯 Impacto Reducción Tasa", "📊 Datos Detallados"])

# TAB 1: OVERVIEW
with tab1:
    st.header("Resumen Ejecutivo")

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)

    saldo_inicial = df['saldo_rem'].iloc[0]
    saldo_actual = df['saldo_rem'].iloc[-1]
    crecimiento_total = ((saldo_actual / saldo_inicial) - 1) * 100

    with col1:
        st.metric(
            label="💰 Saldo Actual",
            value=f"${saldo_actual:,.0f}M",
            delta=f"+${saldo_actual - saldo_inicial:,.0f}M"
        )

    with col2:
        st.metric(
            label="📈 Crecimiento Total",
            value=f"{crecimiento_total:.1f}%",
            delta=f"{crecimiento_total:.1f}% YTD"
        )

    with col3:
        mau_actual = int(df['mau_rem'].iloc[-1])
        mau_inicial = int(df['mau_rem'].iloc[0])
        st.metric(
            label="👥 MAU Actual",
            value=f"{mau_actual:,}",
            delta=f"+{mau_actual - mau_inicial:,}"
        )

    with col4:
        saldo_por_mau_actual = df['saldo_por_mau'].iloc[-1]
        st.metric(
            label="💵 Saldo/MAU",
            value=f"${saldo_por_mau_actual:,.0f}",
            delta=f"${saldo_por_mau_actual - df['saldo_por_mau'].iloc[0]:,.0f}"
        )

    st.markdown("---")

    # Gráfico principal - Evolución del saldo
    st.subheader("Evolución del Saldo REM 2025")

    fig_saldo = go.Figure()

    fig_saldo.add_trace(go.Scatter(
        x=df['fecha'],
        y=df['saldo_rem'],
        mode='lines',
        name='Saldo REM',
        line=dict(color='#2E86AB', width=2),
        fill='tozeroy',
        fillcolor='rgba(46, 134, 171, 0.2)'
    ))

    fig_saldo.add_trace(go.Scatter(
        x=df['fecha'],
        y=df['saldo_ma7'],
        mode='lines',
        name='Media Móvil 7d',
        line=dict(color='#F18F01', width=2, dash='dash')
    ))

    # Línea vertical para reducción de tasa
    fig_saldo.add_vline(
        x=fecha_reduccion_tasa.timestamp() * 1000,
        line_dash="dash",
        line_color="red",
        annotation_text="Reducción de Tasa",
        annotation_position="top"
    )

    fig_saldo.update_layout(
        height=500,
        hovermode='x unified',
        xaxis_title="Fecha",
        yaxis_title="Saldo (Millones CLP)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_saldo, width='stretch')

    # Dos columnas para gráficos adicionales
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("MAU REM - Evolución")
        fig_mau = go.Figure()
        fig_mau.add_trace(go.Scatter(
            x=df['fecha'],
            y=df['mau_rem'],
            mode='lines',
            fill='tozeroy',
            line=dict(color='#A23B72', width=2),
            fillcolor='rgba(162, 59, 114, 0.2)'
        ))
        fig_mau.update_layout(height=300, xaxis_title="Fecha", yaxis_title="MAU")
        st.plotly_chart(fig_mau, width='stretch')

    with col2:
        st.subheader("DAU/MAU Ratio (Engagement)")
        fig_engagement = go.Figure()
        fig_engagement.add_trace(go.Scatter(
            x=df['fecha'],
            y=df['dau_mau_ratio'],
            mode='lines',
            fill='tozeroy',
            line=dict(color='#6A994E', width=2),
            fillcolor='rgba(106, 153, 78, 0.2)'
        ))
        fig_engagement.update_layout(height=300, xaxis_title="Fecha", yaxis_title="DAU/MAU %")
        st.plotly_chart(fig_engagement, width='stretch')

# TAB 2: VELOCIDAD DE CRECIMIENTO
with tab2:
    st.header("Velocidad de Crecimiento del Saldo")

    # Métricas de velocidad
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📅 Crecimiento Diario Promedio",
            value=f"${df['saldo_crecimiento_absoluto_diario'].mean():,.0f}M",
            delta=f"{df['saldo_crecimiento_pct_diario'].mean():.3f}%"
        )

    with col2:
        st.metric(
            label="📆 Crecimiento Semanal Promedio",
            value=f"${df['saldo_crecimiento_absoluto_semanal'].mean():,.0f}M",
            delta=f"{df['saldo_crecimiento_pct_semanal'].mean():.2f}%"
        )

    with col3:
        crecimiento_mensual_abs = df['saldo_rem'].diff(30).mean()
        crecimiento_mensual_pct = ((df['saldo_rem'] / df['saldo_rem'].shift(30)) - 1).mean() * 100
        st.metric(
            label="📊 Crecimiento Mensual Promedio",
            value=f"${crecimiento_mensual_abs:,.0f}M",
            delta=f"{crecimiento_mensual_pct:.2f}%"
        )

    st.markdown("---")

    # Gráfico de crecimiento diario
    st.subheader("Crecimiento Diario Absoluto")

    fig_crecimiento = go.Figure()

    colors = ['#28a745' if x > 0 else '#dc3545' for x in df['saldo_crecimiento_absoluto_diario']]

    fig_crecimiento.add_trace(go.Bar(
        x=df['fecha'],
        y=df['saldo_crecimiento_absoluto_diario'],
        marker_color=colors,
        name='Crecimiento Diario',
        opacity=0.6
    ))

    fig_crecimiento.add_trace(go.Scatter(
        x=df['fecha'],
        y=df['saldo_crecimiento_absoluto_diario'].rolling(7).mean(),
        mode='lines',
        name='Media Móvil 7d',
        line=dict(color='black', width=2)
    ))

    fig_crecimiento.add_vline(
        x=fecha_reduccion_tasa.timestamp() * 1000,
        line_dash="dash",
        line_color="red",
        annotation_text="Reducción de Tasa"
    )

    fig_crecimiento.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

    fig_crecimiento.update_layout(
        height=400,
        xaxis_title="Fecha",
        yaxis_title="Cambio Diario (Millones CLP)",
        hovermode='x unified'
    )

    st.plotly_chart(fig_crecimiento, width='stretch')

    # Análisis mensual
    st.subheader("Análisis Mensual")

    df['año_mes'] = df['fecha'].dt.to_period('M').astype(str)
    resumen_mensual = df.groupby('año_mes').agg({
        'saldo_rem': ['first', 'last', 'mean'],
        'saldo_crecimiento_absoluto_diario': 'mean'
    }).round(2)

    resumen_mensual.columns = ['Saldo_Inicial', 'Saldo_Final', 'Saldo_Promedio', 'Crecimiento_Diario_Promedio']
    resumen_mensual['Crecimiento_Total'] = resumen_mensual['Saldo_Final'] - resumen_mensual['Saldo_Inicial']
    resumen_mensual['Crecimiento_Pct'] = ((resumen_mensual['Saldo_Final'] / resumen_mensual['Saldo_Inicial']) - 1) * 100
    resumen_mensual = resumen_mensual.reset_index()

    # Gráfico de barras del crecimiento mensual
    fig_mensual = go.Figure()

    colors_mensual = ['#28a745' if x > 0 else '#dc3545' for x in resumen_mensual['Crecimiento_Total']]

    fig_mensual.add_trace(go.Bar(
        x=resumen_mensual['año_mes'],
        y=resumen_mensual['Crecimiento_Total'],
        marker_color=colors_mensual,
        text=resumen_mensual['Crecimiento_Total'].round(0),
        texttemplate='%{text:,.0f}M',
        textposition='outside'
    ))

    fig_mensual.update_layout(
        height=400,
        xaxis_title="Mes",
        yaxis_title="Crecimiento Mensual (Millones CLP)",
        showlegend=False
    )

    st.plotly_chart(fig_mensual, width='stretch')

    # Tabla de resumen mensual
    st.dataframe(
        resumen_mensual.style.format({
            'Saldo_Inicial': '${:,.0f}M',
            'Saldo_Final': '${:,.0f}M',
            'Saldo_Promedio': '${:,.0f}M',
            'Crecimiento_Diario_Promedio': '${:,.0f}M',
            'Crecimiento_Total': '${:,.0f}M',
            'Crecimiento_Pct': '{:.2f}%'
        }),
        width='stretch'
    )

# TAB 3: IMPACTO REDUCCIÓN DE TASA
with tab3:
    st.header("🎯 Impacto de la Reducción de Tasa (21-dic-2025)")

    st.warning("⚠️ El 21 de diciembre de 2025 se redujo la tasa de interés entregada a clientes")

    # Comparación antes/después
    st.subheader("Comparación: Antes vs Después del 21-dic")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📅 ANTES (01-ene a 20-dic)")
        dias_antes = len(df_antes)
        saldo_inicial_antes = df_antes['saldo_rem'].iloc[0]
        saldo_final_antes = df_antes['saldo_rem'].iloc[-1]
        crecimiento_antes = ((saldo_final_antes / saldo_inicial_antes) - 1) * 100
        velocidad_diaria_antes = df_antes['saldo_crecimiento_absoluto_diario'].mean()
        velocidad_pct_antes = df_antes['saldo_crecimiento_pct_diario'].mean()

        st.metric("Días analizados", f"{dias_antes}")
        st.metric("Saldo inicial", f"${saldo_inicial_antes:,.0f}M")
        st.metric("Saldo final", f"${saldo_final_antes:,.0f}M")
        st.metric("Crecimiento total", f"{crecimiento_antes:.2f}%")
        st.metric("Velocidad diaria", f"${velocidad_diaria_antes:,.0f}M/día", delta=f"{velocidad_pct_antes:.3f}%/día")

    with col2:
        st.markdown("### 📅 DESPUÉS (21-dic en adelante)")
        if len(df_despues) > 0:
            dias_despues = len(df_despues)
            saldo_inicial_despues = df_despues['saldo_rem'].iloc[0]
            saldo_final_despues = df_despues['saldo_rem'].iloc[-1]
            crecimiento_despues = ((saldo_final_despues / saldo_inicial_despues) - 1) * 100 if saldo_inicial_despues > 0 else 0
            velocidad_diaria_despues = df_despues['saldo_crecimiento_absoluto_diario'].mean()
            velocidad_pct_despues = df_despues['saldo_crecimiento_pct_diario'].mean()

            st.metric("Días analizados", f"{dias_despues}")
            st.metric("Saldo inicial", f"${saldo_inicial_despues:,.0f}M")
            st.metric("Saldo final", f"${saldo_final_despues:,.0f}M")
            st.metric("Crecimiento total", f"{crecimiento_despues:.2f}%")
            st.metric("Velocidad diaria", f"${velocidad_diaria_despues:,.0f}M/día", delta=f"{velocidad_pct_despues:.3f}%/día")

    st.markdown("---")

    # Impacto medido
    if len(df_despues) > 0:
        st.subheader("📊 Impacto Medido")

        cambio_velocidad_diaria = velocidad_diaria_despues - velocidad_diaria_antes
        cambio_velocidad_pct = ((velocidad_pct_despues / velocidad_pct_antes) - 1) * 100

        col1, col2, col3 = st.columns(3)

        with col1:
            delta_color = "inverse" if cambio_velocidad_diaria < 0 else "normal"
            st.metric(
                "Cambio en velocidad diaria",
                f"${cambio_velocidad_diaria:+,.0f}M/día",
                delta=f"{cambio_velocidad_pct:+.2f}%",
                delta_color=delta_color
            )

        with col2:
            cambio_tasa_diaria = velocidad_pct_despues - velocidad_pct_antes
            st.metric(
                "Cambio en tasa de crecimiento diario",
                f"{cambio_tasa_diaria:+.3f} pp",
                delta=f"{cambio_velocidad_pct:+.2f}%",
                delta_color=delta_color
            )

        with col3:
            if cambio_velocidad_diaria < 0:
                st.error("⚠️ La velocidad de crecimiento DISMINUYÓ")
            else:
                st.success("✅ La velocidad se mantuvo o aumentó")

        # Gráfico comparativo
        st.subheader("Comparación Visual")

        fig_comparacion = go.Figure()

        fig_comparacion.add_trace(go.Bar(
            x=['Antes 21-dic', 'Después 21-dic'],
            y=[velocidad_diaria_antes, velocidad_diaria_despues],
            marker_color=['#2E86AB', '#F18F01'],
            text=[f'${velocidad_diaria_antes:,.0f}M', f'${velocidad_diaria_despues:,.0f}M'],
            textposition='outside',
            textfont=dict(size=14, color='black', family='Arial Black')
        ))

        fig_comparacion.update_layout(
            title="Velocidad Promedio de Crecimiento Diario",
            yaxis_title="Crecimiento Diario Promedio (Millones CLP)",
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig_comparacion, width='stretch')

        # Análisis de 7 días antes y después
        st.subheader("Análisis Detallado: 7 días antes y después del 21-dic")

        ventana = df[(df['fecha'] >= fecha_reduccion_tasa - timedelta(days=7)) &
                     (df['fecha'] <= fecha_reduccion_tasa + timedelta(days=7))].copy()

        fig_ventana = go.Figure()

        colors_ventana = ['#2E86AB' if fecha < fecha_reduccion_tasa else '#F18F01' for fecha in ventana['fecha']]

        fig_ventana.add_trace(go.Bar(
            x=ventana['fecha'],
            y=ventana['saldo_crecimiento_absoluto_diario'],
            marker_color=colors_ventana,
            text=ventana['saldo_crecimiento_absoluto_diario'].round(0),
            texttemplate='%{text:+,.0f}M',
            textposition='outside'
        ))

        fig_ventana.add_vline(
            x=fecha_reduccion_tasa.timestamp() * 1000,
            line_dash="dash",
            line_color="red",
            line_width=3,
            annotation_text="REDUCCIÓN DE TASA",
            annotation_position="top"
        )

        fig_ventana.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

        fig_ventana.update_layout(
            title="Crecimiento Diario: 7 días antes y después",
            xaxis_title="Fecha",
            yaxis_title="Cambio Diario (Millones CLP)",
            height=400
        )

        st.plotly_chart(fig_ventana, width='stretch')

        # Tabla detallada
        ventana_display = ventana[['fecha', 'saldo_rem', 'saldo_crecimiento_absoluto_diario', 'saldo_crecimiento_pct_diario']].copy()
        ventana_display['Período'] = ventana_display['fecha'].apply(lambda x: '🔵 Antes' if x < fecha_reduccion_tasa else '🟠 Después')
        ventana_display['Es reducción'] = ventana_display['fecha'] == fecha_reduccion_tasa

        st.dataframe(
            ventana_display.style.format({
                'saldo_rem': '${:,.0f}M',
                'saldo_crecimiento_absoluto_diario': '${:+,.0f}M',
                'saldo_crecimiento_pct_diario': '{:+.2f}%'
            }).apply(lambda x: ['background-color: #ffebee' if x['Es reducción'] else '' for _ in range(len(x))], axis=1),
            width='stretch'
        )

# TAB 4: DATOS DETALLADOS
with tab4:
    st.header("📊 Datos Detallados")

    st.subheader("Top Eventos")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚀 Top 10 Mayores Crecimientos")
        top_crecimientos = df.nlargest(10, 'saldo_crecimiento_absoluto_diario')[
            ['fecha', 'saldo_rem', 'saldo_crecimiento_absoluto_diario', 'saldo_crecimiento_pct_diario']
        ]
        st.dataframe(
            top_crecimientos.style.format({
                'saldo_rem': '${:,.0f}M',
                'saldo_crecimiento_absoluto_diario': '${:+,.0f}M',
                'saldo_crecimiento_pct_diario': '{:+.2f}%'
            }),
            width='stretch'
        )

    with col2:
        st.markdown("### 📉 Top 10 Mayores Decrecimientos")
        top_decrecimientos = df.nsmallest(10, 'saldo_crecimiento_absoluto_diario')[
            ['fecha', 'saldo_rem', 'saldo_crecimiento_absoluto_diario', 'saldo_crecimiento_pct_diario']
        ]
        st.dataframe(
            top_decrecimientos.style.format({
                'saldo_rem': '${:,.0f}M',
                'saldo_crecimiento_absoluto_diario': '${:+,.0f}M',
                'saldo_crecimiento_pct_diario': '{:+.2f}%'
            }),
            width='stretch'
        )

    st.markdown("---")

    # Dataset completo
    st.subheader("📋 Dataset Completo")

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", value=df['fecha'].min().date())
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=df['fecha'].max().date())

    df_filtrado = df[(df['fecha'] >= pd.to_datetime(fecha_inicio)) & (df['fecha'] <= pd.to_datetime(fecha_fin))]

    st.dataframe(
        df_filtrado[['fecha', 'saldo_rem', 'mau_rem', 'dau_rem', 'saldo_crecimiento_absoluto_diario',
                     'saldo_crecimiento_pct_diario', 'saldo_por_mau', 'dau_mau_ratio']].style.format({
            'saldo_rem': '${:,.0f}M',
            'mau_rem': '{:,.0f}',
            'dau_rem': '{:,.0f}',
            'saldo_crecimiento_absoluto_diario': '${:+,.0f}M',
            'saldo_crecimiento_pct_diario': '{:+.2f}%',
            'saldo_por_mau': '${:,.0f}',
            'dau_mau_ratio': '{:.2f}%'
        }),
        width='stretch',
        height=400
    )

    # Descargar datos
    st.subheader("💾 Descargar Datos")

    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f'datos_rem_{fecha_inicio}_{fecha_fin}.csv',
        mime='text/csv',
    )

# Footer
st.markdown("---")
st.markdown("**📅 Última actualización:** " + df['fecha'].max().strftime('%Y-%m-%d'))
st.markdown("**💻 Generado por:** Análisis de Cuenta Remunerada - Tenpo")
