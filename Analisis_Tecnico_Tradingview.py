import streamlit as st
from tradingview_ta import TA_Handler, Interval
from datetime import datetime
import pandas as pd
import requests

def format_indicator_value(value):
    return f"{float(value):.2f}" if isinstance(value, (float, int)) else str(value)

def get_last_price(symbol, exchange):
    try:
        if exchange == "BCBA":
            # Usar la API de TradingView para obtener el precio
            handler = TA_Handler(
                symbol=symbol,
                exchange=exchange,
                screener="argentina",
                interval=Interval.INTERVAL_1_DAY
            )
            analysis = handler.get_analysis()
            # El precio de cierre está en los indicadores
            return analysis.indicators['close']
        return None
    except:
        return None

def analizar_activo(simbolo="GGAL", exchange="BCBA", intervalo=Interval.INTERVAL_1_DAY):
    handler = TA_Handler(
        symbol=simbolo,
        exchange=exchange,
        screener="argentina",
        interval=intervalo
    )
    
    try:
        analysis = handler.get_analysis()
        # Guardar el precio de cierre junto con el análisis
        analysis.last_price = analysis.indicators['close']
        return analysis
    except Exception as e:
        st.error(f"Error en el análisis: {str(e)}")
        return None

def main():
    # Configuración de la página
    st.set_page_config(
        page_title="Análisis Técnico - Trading View",
        page_icon="📈",
        layout="wide"
    )

    # Título principal
    st.title("📊 Análisis Técnico - Trading View")

    # Sidebar para configuración
    with st.sidebar:
        st.header("Configuración")
        simbolo = st.text_input("Símbolo", value="GGAL").upper()
        exchange = st.text_input("Exchange", value="BCBA").upper()
        intervalo = st.selectbox(
            "Intervalo",
            options=[
                Interval.INTERVAL_1_MINUTE, 
                Interval.INTERVAL_5_MINUTES,
                Interval.INTERVAL_15_MINUTES,
                Interval.INTERVAL_30_MINUTES,
                Interval.INTERVAL_1_HOUR,
                Interval.INTERVAL_2_HOURS,
                Interval.INTERVAL_4_HOURS,
                Interval.INTERVAL_1_DAY,
                Interval.INTERVAL_1_WEEK,
                Interval.INTERVAL_1_MONTH
            ],
            index=7  # Default a 1 día
        )
        
        if st.button("Analizar"):
            with st.spinner('Analizando...'):
                analysis = analizar_activo(simbolo, exchange, intervalo)
                if analysis:
                    st.session_state['analysis'] = analysis
                    st.session_state['timestamp'] = datetime.now()
                    # El precio ya está incluido en el análisis
                    st.session_state['last_price'] = analysis.last_price

    # Verificar si hay análisis en la sesión
    if 'analysis' in st.session_state:
        analysis = st.session_state['analysis']
        timestamp = st.session_state['timestamp']
        last_price = st.session_state.get('last_price', 'N/A')
        
        # Formatear el precio si está disponible
        price_display = f"${last_price:.2f}" if isinstance(last_price, (float, int)) else "N/A"

        # Mostrar ticker y precio en un contenedor destacado
        st.markdown(f"""
        <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px'>
            <h1 style='text-align: center; color: #0e1117; margin: 0;'>{simbolo} ({exchange})</h1>
            <h2 style='text-align: center; color: #0e1117; margin: 10px 0;'>
                Último Precio: {price_display}
            </h2>
            <p style='text-align: center; color: #666; margin: 0;'>
                Actualizado: {timestamp.strftime('%d-%m-%Y %H:%M:%S')}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Crear dos columnas para la primera fila
        col1, col2 = st.columns(2)

        # Columna 1: Indicadores Principales
        with col1:
            st.subheader("📊 Indicadores Principales")
            indicators = {
                "RSI(14)": "RSI",
                "EMA(20)": "EMA20",
                "SMA(20)": "SMA20",
                "MACD": "MACD.macd",
                "MACD Signal": "MACD.signal"
            }
            
            indicators_data = {
                name: format_indicator_value(analysis.indicators[key])
                for name, key in indicators.items()
            }
            
            st.dataframe(
                pd.DataFrame(indicators_data.items(), columns=['Indicador', 'Valor'])
                .set_index('Indicador'),
                use_container_width=True
            )

        # Columna 2: Análisis de Tendencia
        with col2:
            st.subheader("📈 Análisis de Tendencia (ADX)")
            adx = analysis.indicators['ADX']
            adx_plus = analysis.indicators['ADX+DI']
            adx_minus = analysis.indicators['ADX-DI']
            
            adx_data = {
                'Indicador': ['ADX', 'DI+', 'DI-'],
                'Valor': [f"{adx:.2f}", f"{adx_plus:.2f}", f"{adx_minus:.2f}"]
            }
            st.dataframe(
                pd.DataFrame(adx_data).set_index('Indicador'),
                use_container_width=True
            )

            st.subheader("🎯 Interpretación ADX")
            if adx > 25:
                trend = "FUERTE" if adx > 25 else "DÉBIL"
                direction = "ALCISTA" if adx_plus > adx_minus else "BAJISTA"
                st.write(f"• Tendencia {trend} ({direction})")
                st.progress(adx/100, text=f"Fuerza de la tendencia: {adx:.2f}%")
            else:
                st.write("• Tendencia DÉBIL o LATERAL")
                st.progress(adx/100, text=f"Fuerza de la tendencia: {adx:.2f}%")

        # Segunda fila: Recomendaciones
        st.subheader("💡 Recomendaciones")
        rec_col1, rec_col2, rec_col3 = st.columns(3)

        with rec_col1:
            st.metric("Compra", analysis.summary['BUY'])
        with rec_col2:
            st.metric("Neutral", analysis.summary['NEUTRAL'])
        with rec_col3:
            st.metric("Venta", analysis.summary['SELL'])

        # Mostrar recomendación general
        recomendacion = analysis.summary['RECOMMENDATION']
        color = {
            'BUY': '#28a745',
            'SELL': '#dc3545',
            'NEUTRAL': '#6c757d'
        }.get(recomendacion, '#000000')
        
        st.markdown(f"""
        <div style='text-align: center; padding: 15px; background-color: {color}; color: white; border-radius: 10px; margin: 20px 0;'>
            <h3 style='margin: 0;'>Recomendación General: {recomendacion}</h3>
        </div>
        """, unsafe_allow_html=True)

        # Tercera fila: Análisis por Tipo
        st.subheader("🔍 Análisis por Tipo")
        type_col1, type_col2 = st.columns(2)

        with type_col1:
            st.metric("Osciladores", analysis.oscillators['RECOMMENDATION'])
        with type_col2:
            st.metric("Medias Móviles", analysis.moving_averages['RECOMMENDATION'])

if __name__ == "__main__":
    main()
