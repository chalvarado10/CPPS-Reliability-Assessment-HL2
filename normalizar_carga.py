import pandas as pd
def normalizar_carga(df):
    """
    Normaliza la potencia a valores en por de carga en (pu)
    Argunmentos: Dataframe con columnas de kW
    Retorna: Dataframe con carga en p.u."""
    #Verificar si el DataFrame está vacío
    if df.empty:
        raise ValueError("El DataFrame está vacío.")
    #Verificar si la columnas existen:
    if 'kW' not in df.columns:
        raise ValueError("El DataFrame no contiene la columna 'kW'")
    # Calcular la potencia base
    potencia_base = max(df['kW'])
    if potencia_base <= 0:
        raise ValueError("La potencia base debe ser mayor que cero.")
    # Normalizar la carga en p.u.
    df['pu'] = df['kW'] / potencia_base
    columns = ['hora', 'pu']
    df_normalizado = df[columns]
    return df_normalizado