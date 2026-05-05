def tasa_falla_scada(p_ied, n_ied, p_switch, n_switch, p_server, n_server, p_cl, n_cl):
    """Para la aplicacion de la funcion se detallan los siguientes parametros:
    p_ied: tasa de falla del IED
    P_switch: tasa de falla del switch
    p_server: tasa de falla del servidor
    p_cl: tasa de falla de las lineas de comunicación
    Retorna : tasa de falla del sistema SCADA incluyendo ataque cibernético
    n = es el número de ataques cibernéticos por unidad de tiempo
    k = es el coficiente de seguridad del sistema cibernético que representa la capacidad de defensa contra cyberataques"""
    import numpy as np
    n = 5000
    k = 500
    producto = 1.0

    # Lista de componentes con número de repeticiones
    componentes = [(p_server, n_server), (p_switch, n_switch), (p_ied, n_ied), (p_cl, n_cl)]

    for p, n in componentes:
        producto *= (1 - p) ** n
    p_scada = 1 - producto
    print(p_scada)
    p_exito_ataque = 1 - np.exp(-n/k)
    pf = 1-(p_scada*(1 - p_exito_ataque))
    u = 1/48 # tasa de restauración del sistema luego de un ataque exitoso
    l_scada = pf*u/(1-u)
    return pf, u, l_scada

# Definimos tasas de falla y restauración para cada componente por hora
# p_ied, n_ied, p_switch, n_switch, p_server, n_server, p_cl, n_cl = [(168000/(48+168000)), 5, (438000/(48+438000)), 1, (125000/(48+125000)), 1, (11750000/(48+11750000)), 1]

# df = tasa_falla_scada(p_ied, n_ied, p_switch, n_switch, p_server, n_server, p_cl, n_cl)