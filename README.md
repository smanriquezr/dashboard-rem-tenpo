# 📊 Dashboard de Análisis - Cuenta Remunerada 2025

Dashboard interactivo desarrollado con Streamlit para analizar el comportamiento del saldo, MAU y el impacto de la reducción de tasa del 21 de diciembre de 2025.

## 🚀 Demo en Vivo

[Ver Dashboard](https://tu-usuario-rem-dashboard.streamlit.app) _(actualiza este enlace después del despliegue)_

## 📸 Preview

El dashboard incluye:
- 📈 Overview con métricas principales
- ⚡ Análisis de velocidad de crecimiento
- 🎯 Impacto de reducción de tasa (21-dic-2025)
- 📊 Datos detallados y descargables

## ✨ Características

- **Métricas en tiempo real**: Saldo actual, crecimiento, MAU, engagement
- **Visualizaciones interactivas**: Gráficos con Plotly (zoom, pan, hover)
- **Análisis comparativo**: Antes vs después de reducción de tasa
- **Descarga de datos**: Exporta datos filtrados en CSV
- **Responsive**: Funciona en desktop y mobile

## 🛠️ Tecnologías

- Python 3.11+
- Streamlit
- Plotly
- Pandas
- pandas-gbq (BigQuery)

## 📦 Instalación Local

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/tu-repo.git
cd tu-repo

# Instalar dependencias
pip install -r requirements_streamlit.txt

# Ejecutar la aplicación
streamlit run app_analisis_rem.py
```

La app estará disponible en `http://localhost:8501`

## 🌐 Despliegue en Streamlit Cloud

1. Fork este repositorio
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio y `app_analisis_rem.py`
5. Click en "Deploy"

## 📊 Insights Principales

### Crecimiento Explosivo
- **+335.69%** de crecimiento en 2025
- De $52,271M a $227,742M

### Impacto de Reducción de Tasa (21-dic-2025)
- ⚠️ Velocidad de crecimiento cayó **-63.48%**
- Antes: $482.79M/día → Después: $336.41M/día

### Engagement Alto
- DAU/MAU promedio: **71.80%**

## 📁 Estructura del Proyecto

```
.
├── app_analisis_rem.py              # Aplicación principal
├── requirements_streamlit.txt       # Dependencias
├── datos_saldo_detallado.csv        # Datos procesados
├── README.md                        # Este archivo
└── .gitignore                       # Archivos excluidos de Git
```

## ⚙️ Configuración

La aplicación tiene dos modos de carga de datos:

1. **CSV Local** (por defecto): Usa `datos_saldo_detallado.csv`
2. **BigQuery**: Carga datos frescos desde BigQuery (requiere autenticación)

Puedes cambiar entre modos usando el checkbox "Usar datos guardados" en el sidebar.

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es de uso interno de Tenpo.

## 👥 Autores

- Equipo de BI - Tenpo

## 📧 Contacto

Para preguntas o soporte, contacta al equipo de BI.

---

**Última actualización**: Enero 2026
