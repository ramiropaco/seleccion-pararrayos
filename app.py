import streamlit as st
import math
import pandas as pd
import altair as alt

# Configuración de la página
st.set_page_config(
    page_title="Cálculo de Selección de Pararrayos",
    page_icon="⚡",
    layout="wide"
)

st.title("📊 Cálculo de Selección de Pararrayos")
st.subheader("Análisis Técnico para Subestaciones Eléctricas")

# Crear columnas para organizar la interfaz
col1, col2 = st.columns([1, 1.5])

with col1:
    st.header("Parámetros de Entrada")
    
    # Parámetros del sistema
    st.subheader("Parámetros del Sistema")
    U_m = st.number_input("Tensión máxima del sistema (U_m) [kV]", 
                         min_value=100.0, max_value=500.0, value=245.0, step=1.0,
                         help="Tensión máxima del sistema en kilovoltios")
    
    K_e = st.number_input("Factor de falla a tierra (K_e)", 
                         min_value=1.0, max_value=2.0, value=1.4, step=0.1,
                         help="Factor de falla a tierra (1.4 para sistema sólidamente puesto a tierra)")
    
    k_d = st.number_input("Factor de diseño (k_d)", 
                         min_value=0.5, max_value=0.95, value=0.8, step=0.05,
                         help="Factor de diseño típico de catálogos de fabricantes")
    
    k_tov = st.number_input("Capacidad del pararrayos contra sobretensiones temporales (k_TOV)", 
                           min_value=1.0, max_value=1.5, value=1.15, step=0.05,
                           help="Capacidad del pararrayos para sobretensiones temporales de 1s de duración")
    
    # Parámetros de los aisladores
    st.subheader("Parámetros de los Aisladores")
    num_insulators = st.number_input("Número de aisladores en la cadena", 
                                    min_value=10, max_value=50, value=23, step=1,
                                    help="Incluyendo 2 extra para contraflameo")
    
    insulator_length = st.number_input("Longitud nominal de un aislador [m]", 
                                      min_value=0.1, max_value=0.5, value=0.146, step=0.001,
                                      format="%.3f",
                                      help="Longitud nominal de un aislador cerámico en metros")
    
    sigma = st.number_input("Desviación estándar de probabilidad de flameo (σ)", 
                           min_value=0.01, max_value=0.1, value=0.03, step=0.01,
                           format="%.2f",
                           help="Desviación estándar para la probabilidad de flameo")
    
    # Parámetros de la línea
    st.subheader("Parámetros de la Línea")
    system_voltage = st.number_input("Tensión del sistema para selección de impedancia [kV]", 
                                    min_value=100.0, max_value=500.0, value=245.0, step=1.0,
                                    help="Tensión del sistema para la selección de la impedancia característica")
    
    # La impedancia característica se selecciona automáticamente según la tensión del sistema
    if system_voltage < 145:
        Z_0 = 450
    elif 145 <= system_voltage <= 345:
        Z_0 = 400
    else:
        Z_0 = 350
    
    st.info(f"Impedancia característica (Z_0): {Z_0} Ω (seleccionada automáticamente según la tensión del sistema)")
    
    U_res = st.number_input("Tensión residual al impulso tipo rayo [kVp]", 
                           min_value=300, max_value=600, value=452, step=1,
                           help="Tensión residual al impulso tipo rayo (de catálogo)")
    
    line_length = st.number_input("Longitud de la línea [km]", 
                                 min_value=1.0, max_value=100.0, value=22.94, step=0.1,
                                 help="Longitud de la línea en kilómetros")
    
    v = st.number_input("Velocidad de propagación de la onda [km/μs]", 
                       min_value=0.2, max_value=0.4, value=0.3, step=0.01,
                       help="Velocidad de propagación de la onda (típicamente 0.3 km/μs)")
    
    N = st.number_input("Número de líneas conectadas", 
                       min_value=1, max_value=5, value=1, step=1,
                       help="Número de líneas conectadas (se asume 1)")
    
    n = st.number_input("Número de descargas consecutivas", 
                       min_value=1, max_value=5, value=2, step=1,
                       help="Número de descargas consecutivas (2, según IEC)")

# Funciones de cálculo
def calculate_cov(U_m):
    """Calcula la tensión máxima de operación continua (COV)"""
    return 1.05 * (U_m / math.sqrt(3))

def calculate_tov(cov, K_e):
    """Calcula la máxima sobretensión temporal (TOV)"""
    return K_e * cov

def calculate_rated_voltage(cov, tov, k_d, k_tov):
    """Determina la tensión nominal del pararrayos"""
    U_r1 = cov / k_d
    U_r2 = tov / k_tov
    return max(U_r1, U_r2), U_r1, U_r2

def normalized_rated_voltage(U_r_theoretical):
    """Selecciona la tensión nominal normalizada del catálogo"""
    # Ejemplo de valores estándar de catálogo
    standard_values = [96, 108, 120, 144, 156, 168, 180, 192, 216, 228, 240, 258, 264, 276, 288, 300, 312, 330, 336, 360, 396]
    
    # Seleccionar el valor estándar más cercano por encima del valor teórico
    for value in standard_values:
        if value >= U_r_theoretical:
            return value
    
    # Si no hay un valor adecuado, devolver el último de la lista
    return standard_values[-1]

def calculate_incident_voltage(num_insulators, insulator_length, sigma):
    """Calcula la tensión incidente con 90% de probabilidad de no flameo"""
    w = num_insulators * insulator_length
    V_50 = 550 * w
    V_i = V_50 * (1 - 1.3 * sigma)
    return V_i, V_50, w

def calculate_discharge_current(V_i, Z_0):
    """Calcula la corriente de descarga"""
    I_d = (2 * V_i) / Z_0
    
    # Seleccionar la corriente nominal estándar
    if I_d <= 5:
        I_d_nominal = 5
    elif I_d <= 10:
        I_d_nominal = 10
    elif I_d <= 20:
        I_d_nominal = 20
    else:
        I_d_nominal = 20  # Máximo valor estándar
        
    return I_d, I_d_nominal

def calculate_energy_absorption(V_50, U_res, U_r, Z_0, line_length, v, N, n):
    """Calcula la absorción de energía para determinar la clase de descarga de línea"""
    T_w = line_length / v
    W = (2 * V_50 - N * U_res * (1 + math.log(2 * V_50 / U_res))) * (U_res * T_w * n) / Z_0
    W_prime = W / (U_r * 1000)  # Convertir W a kJ para el cálculo de W_prime
    
    # Determinar la clase de descarga de línea
    if W_prime <= 1:
        discharge_class = 1
    elif W_prime <= 2:
        discharge_class = 2
    elif W_prime <= 3:
        discharge_class = 3
    elif W_prime <= 4:
        discharge_class = 4
    else:
        discharge_class = 5
        
    return W, W_prime, T_w, discharge_class

def estimate_switching_impulse_protection_level(U_r):
    """Estima el nivel de protección para el impulso de maniobra (NPM)"""
    # Esta es una estimación basada en catálogos típicos (aproximadamente 2x la tensión nominal)
    return round(U_r * 1.85)

# Botón para realizar los cálculos
if st.sidebar.button("Calcular", type="primary"):
    with col2:
        st.header("Resultados de los Cálculos")
        
        # Crear contenedores ampliables para cada sección de cálculos
        with st.expander("3.11.1 Tensión máxima de operación continua (COV)", expanded=True):
            cov = calculate_cov(U_m)
            
            st.markdown(f"""
            **COV = {cov:.2f} kV**
            
            *Fórmula:* COV = 1.05 * (U_m / √3) = 1.05 * ({U_m} / √3) = {cov:.2f} kV
            
            *Explicación:* COV es la tensión eficaz máxima que el pararrayos puede manejar continuamente.
            """)
            
        with st.expander("3.11.2 Máxima sobretensión temporal (TOV)", expanded=True):
            tov = calculate_tov(cov, K_e)
            
            st.markdown(f"""
            **TOV = {tov:.2f} kV**
            
            *Fórmula:* TOV = K_e * COV = {K_e} * {cov:.2f} = {tov:.2f} kV
            
            *Explicación:* TOV considera las sobretensiones temporales, por ejemplo, durante fallas a tierra.
            """)
            
        with st.expander("3.11.3 Tensión nominal del pararrayos (U_r)", expanded=True):
            U_r_theoretical, U_r1, U_r2 = calculate_rated_voltage(cov, tov, k_d, k_tov)
            
            st.markdown(f"""
            **U_r1 = {U_r1:.2f} kV** (basado en tensión continua de operación)
            
            *Fórmula:* U_r1 = COV / k_d = {cov:.2f} / {k_d} = {U_r1:.2f} kV
            
            **U_r2 = {U_r2:.2f} kV** (basado en sobretensiones temporales)
            
            *Fórmula:* U_r2 = TOV / k_TOV = {tov:.2f} / {k_tov} = {U_r2:.2f} kV
            
            **Tensión nominal teórica seleccionada (U_r): {U_r_theoretical:.2f} kV**
            
            *Explicación:* U_r es el máximo de U_r1 y U_r2, representando la tensión nominal del pararrayos.
            """)
            
        with st.expander("3.11.4 Tensión nominal normalizada del pararrayos", expanded=True):
            U_r = normalized_rated_voltage(U_r_theoretical)
            
            st.markdown(f"""
            **Tensión nominal normalizada (U_r): {U_r} kV**
            
            *Explicación:* La tensión nominal teórica ({U_r_theoretical:.2f} kV) se redondea al valor estándar más cercano del catálogo.
            """)
            
        with st.expander("3.11.5 Tensión incidente", expanded=True):
            V_i, V_50, w = calculate_incident_voltage(num_insulators, insulator_length, sigma)
            
            st.markdown(f"""
            **Longitud de la cadena de aisladores (w): {w:.3f} m**
            
            *Fórmula:* w = {num_insulators} * {insulator_length} = {w:.3f} m
            
            **Tensión crítica de flameo (V_50%): {V_50:.2f} kV**
            
            *Fórmula:* V_50% = 550 * {w:.3f} = {V_50:.2f} kV
            
            **Tensión incidente (V_i): {V_i:.2f} kV**
            
            *Fórmula:* V_i = {V_50:.2f} * (1 - 1.3 * {sigma}) = {V_i:.2f} kV
            
            *Explicación:* V_i es la tensión con 90% de probabilidad de no flameo.
            """)
            
        with st.expander("3.11.6 Impedancia característica", expanded=True):
            st.markdown(f"""
            **Impedancia característica (Z_0): {Z_0} Ω**
            
            *Explicación:* Z_0 es seleccionada de la tabla IEC 60099-4 para tensión del sistema {system_voltage} kV.
            """)
            
        with st.expander("3.11.7 Corriente nominal de descarga", expanded=True):
            I_d, I_d_nominal = calculate_discharge_current(V_i, Z_0)
            
            st.markdown(f"""
            **Corriente de descarga calculada (I_d): {I_d:.2f} kAp**
            
            *Fórmula:* I_d = (2 * V_i) / Z_0 = (2 * {V_i:.2f}) / {Z_0} = {I_d:.2f} kAp
            
            **Corriente nominal seleccionada (I_d): {I_d_nominal} kAp**
            
            *Explicación:* Se elige una corriente nominal de descarga de {I_d_nominal} kAp ya que supera el valor calculado.
            """)
            
        with st.expander("3.11.8 Clase de descarga de línea", expanded=True):
            W, W_prime, T_w, discharge_class = calculate_energy_absorption(V_50, U_res, U_r, Z_0, line_length, v, N, n)
            
            st.markdown(f"""
            **Tiempo de propagación de la onda (T_w): {T_w:.2f} μs**
            
            *Fórmula:* T_w = {line_length} / {v} = {T_w:.2f} μs
            
            **Energía absorbida (W): {W:.2f} J = {W/1000:.2f} kJ**
            
            *Fórmula:* W = [2 * {V_50:.2f} - {N} * {U_res} * (1 + ln(2 * {V_50:.2f} / {U_res}))] * ({U_res} * {T_w:.2f} * {n}) / {Z_0}
            
            **Capacidad de absorción específica (W'): {W_prime:.2f}**
            
            *Fórmula:* W' = {W/1000:.2f} / {U_r} = {W_prime:.2f}
            
            *Explicación:* W' = {W_prime:.2f} corresponde a la clase de descarga de línea {discharge_class}.
            """)
        
        # Nivel de protección para impulso de maniobra (estimado)
        NPM = estimate_switching_impulse_protection_level(U_r)
            
        # Resumen final
        st.header("Resumen Final de la Selección del Pararrayos")
        
        # Crear un DataFrame para mostrar los resultados en una tabla
        summary_data = {
            "Parámetro": [
                "Tensión nominal normalizada (U_r)", 
                "Corriente nominal de descarga (I_d)", 
                "Clase de descarga de línea", 
                "Nivel de protección (impulso tipo rayo, NPR)", 
                "Nivel de protección (impulso maniobra, NPM)"
            ],
            "Valor": [
                f"{U_r} kV", 
                f"{I_d_nominal} kAp", 
                f"{discharge_class} (basado en W' = {W_prime:.2f})", 
                f"{U_res} kV", 
                f"{NPM} kV (estimado)"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.table(summary_df)
        
        # Visualización de datos con Altair
        st.subheader("Visualización de Resultados")
        
        # Gráfico de barras para comparar tensiones
        voltage_data = pd.DataFrame({
            'Tipo': ['COV', 'TOV', 'U_r1', 'U_r2', 'U_r', 'V_i'],
            'Tensión (kV)': [cov, tov, U_r1, U_r2, U_r, V_i]
        })
        
        voltage_chart = alt.Chart(voltage_data).mark_bar().encode(
            x=alt.X('Tipo', sort=None, title='Tipo de Tensión'),
            y=alt.Y('Tensión (kV)', title='Tensión (kV)'),
            color='Tipo',
            tooltip=['Tipo', 'Tensión (kV)']
        ).properties(
            title='Comparación de Tensiones',
            width=600,
            height=400
        )
        
        st.altair_chart(voltage_chart, use_container_width=True)

        # Mostrar información sobre la selección del pararrayos
        st.info("""
        **Recomendación**: Con base en los resultados obtenidos, se recomienda seleccionar 
        un pararrayos de óxido metálico con las siguientes características:
        """)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.success(f"🔌 **Tensión nominal**: {U_r} kV")
            st.success(f"⚡ **Corriente nominal de descarga**: {I_d_nominal} kA")
            st.success(f"🛡️ **Clase de descarga de línea**: {discharge_class}")
        with col_b:
            st.success(f"🔽 **Nivel de protección (rayo)**: {U_res} kV")
            st.success(f"🔄 **Nivel de protección (maniobra)**: {NPM} kV")

else:
    with col2:
        st.info("👈 Verifique los parámetros de entrada y haga clic en 'Calcular' para ver los resultados.")
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Metal_oxide_surge_arrester.svg/800px-Metal_oxide_surge_arrester.svg.png", 
                 caption="Pararrayos de óxido metálico", width=400)
        
        st.markdown("""
        ### Acerca de esta aplicación
        
        Esta herramienta realiza los cálculos necesarios para la selección adecuada de pararrayos en subestaciones eléctricas, 
        siguiendo los procedimientos establecidos por las normas IEC.
        
        El proceso de cálculo incluye:
        
        1. Determinación de la tensión máxima de operación continua (COV)
        2. Cálculo de la máxima sobretensión temporal (TOV)
        3. Determinación de la tensión nominal del pararrayos (U_r)
        4. Selección de la tensión nominal normalizada
        5. Cálculo de la tensión incidente
        6. Selección de la impedancia característica
        7. Cálculo de la corriente nominal de descarga
        8. Determinación de la clase de descarga de línea
        
        Los valores predeterminados corresponden a un caso de estudio para la subestación Mazocruz.
        """)

# Información adicional en la barra lateral
with st.sidebar:
    st.header("Información")
    st.markdown("""
    Esta aplicación realiza la selección técnica de pararrayos para subestaciones eléctricas.
    
    Ingrese los parámetros requeridos o utilice los valores predeterminados.
    
    **Referencias:**
    - IEC 60099-4: Norma para pararrayos
    - IEEE C62.11: Estándar para pararrayos de óxido metálico para sistemas de CA
    """)
    
    st.markdown("---") 
    st.markdown("© 2025 - Aplicación para Selección de Pararrayos")