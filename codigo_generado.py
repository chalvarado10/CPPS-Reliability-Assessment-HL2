import sys
PFD_path = r"C:\Program Files\DIgSILENT\PowerFactory 2022\Python\3.10"
sys.path.append(PFD_path)
import powerfactory as pf
import numpy as np
import pandas as pd
import random
from scipy.stats.qmc import LatinHypercube

# === Inicializar PowerFactory ===
app = pf.GetApplication()
app.ClearOutputWindow()
ldf = app.GetFromStudyCase("ComLdf")

# === Obtener objetos del sistema ===
lineas = app.GetCalcRelevantObjects("*.ElmLne")
trafos = app.GetCalcRelevantObjects("*.ElmTr2")
generadores = app.GetCalcRelevantObjects("*.ElmSym")
cargas = app.GetCalcRelevantObjects("*.ElmLod")

componentes = {
   #"Linea": lineas,
   #"Trafo": trafos,
    "Generador": generadores,
    "Carga": cargas
}

# === Tasas de falla y reparación (por hora) ===
tasa_falla = {
    "Linea": 2 / 24,
    "Trafo": 1 / 24,
    "Generador": 1.5 / 24,
    "Carga": 0.5 / 24
}
tasa_reparacion = {
    "Linea": 1 / 4,
    "Trafo": 1 / 6,
    "Generador": 1 / 5,
    "Carga": 1 / 3
}

# === Configuración SCADA ===
def calcular_pf(p_ied, p_server, p_switch, p_cl):
    num = np.prod([1 - p for p in p_ied]) * np.prod([1 - p for p in p_server])
    den = np.prod([1 - p for p in p_switch]) * np.prod([1 - p for p in p_cl])
    return 1 - (num / den)

p_ied = [0.01]
p_switch = [0.015]
p_server = [0.02]
p_cl = [0.005]
t_rest_scada = 0.5

# === Cargar curva de carga ===
df_carga = pd.read_csv(r"C:\Users\ASUS\OneDrive\Tesis\Tesis Espol\loadprofile_horaria.csv", sep =',', names = ['hora','kW'])
curva_carga = df_carga['kW'].values
carga_max = curva_carga.max()

# === Identificar barras con cargas conectadas ===
cargas_por_barra = {}
for carga in cargas:
    barra = carga.bus1.cterm
    if barra:
        cargas_por_barra.setdefault(barra.loc_name, []).append(carga)

# === Configuración de simulación ===
n_eventos = 100
lhs = LatinHypercube(d=2)

resultados = []
for i in range(n_eventos):
    app.PrintPlain(f"\n--- EVENTO {i+1} ---")
    hora = random.randint(0, len(curva_carga) - 1)
    carga_actual = curva_carga[hora] / carga_max
    ens_total = 0
    desconectados = []
    resumen_fallas = []
    tiempos_restauracion = {}
    componentes_fallados = set()

    for carga in cargas:
        carga.SetAttribute("plini", carga.GetAttribute("plini") * carga_actual)
        carga.SetAttribute("qlini", carga.GetAttribute("qlini") * carga_actual)

    for gen in generadores:
        gen.SetAttribute("pgini", gen.GetAttribute("pgini") * carga_actual)
        gen.SetAttribute("qgini", gen.GetAttribute("qgini") * carga_actual)

    muestras_tipo = {tipo: lhs.random(len(lista)) for tipo, lista in componentes.items()}

    for tipo, lista in componentes.items():
        for idx, obj in enumerate(lista):
            muestras = muestras_tipo[tipo][idx]
            tf = -np.log(muestras[0]) / tasa_falla[tipo]
            tr = -np.log(muestras[1]) / tasa_reparacion[tipo]

            fallo_fisico = tf < 24
            fallo_scada = random.random() < calcular_pf(p_ied, p_server, p_switch, p_cl)

            if fallo_fisico or fallo_scada:
                obj.outserv = 1
                desconectados.append(obj.loc_name)
                resumen_fallas.append(f"{obj.loc_name} (fisica={fallo_fisico}, scada={fallo_scada})")
                tiempos_restauracion[obj.loc_name] = tr
                componentes_fallados.add(obj.loc_name)

    resultado_ldf = ldf.Execute()

    if resultado_ldf != 0:
        app.PrintPlain(f" El flujo de carga no convergió en el evento {i+1}. Se considera ENS total usando tr según componente responsable.")
        tr_dominante = max([
            tr for nombre, tr in tiempos_restauracion.items()
            if not any(nombre == c.loc_name for c in cargas)
        ] + [0.5])

        ens_total = sum([
            carga.GetAttribute("plini") * tr_dominante
            for carga in cargas
        ])
    else:
        for barra, cargas_barra in cargas_por_barra.items():
            for carga in cargas_barra:
                p_nom = carga.GetAttribute("plini")
                loc_name = carga.loc_name

                if loc_name in tiempos_restauracion:
                    ens_total += p_nom * tiempos_restauracion[loc_name]
                else:
                    try:
                        barra_obj = carga.bus1.cterm
                        p_serv = barra_obj.GetAttribute("m:Psum")

                        if p_serv is not None:
                            p_nom_total = sum(c.GetAttribute("plini") for c in cargas_barra)
                            if p_serv < 0.95 * p_nom_total:
                                tr = max([
                                    tiempos_restauracion.get(nombre, 0.5)
                                    for nombre in tiempos_restauracion
                                ])
                                ens_total += (p_nom_total - p_serv) * tr
                    except Exception as e:
                        app.PrintPlain(f" Error obteniendo potencia para {loc_name}: {e}")

        tr_dominante = max(tiempos_restauracion.values(), default=0.5)

    resultados.append({
        "Evento": i + 1,
        "Hora": hora,
        "ENS_kWh": round(ens_total, 2),
        "TR_dominante": round(tr_dominante, 2),
        "Componentes_fuera": ", ".join(desconectados),
        "Detalle_fallas": "; ".join(resumen_fallas)
    })

    for tipo, lista in componentes.items():
        for obj in lista:
            obj.outserv = 0

# === Guardar resultados ===
df_resultados = pd.DataFrame(resultados)
print(df_resultados)
df_resultados.to_csv("ens_eventos.csv", index=False)
app.PrintPlain("\nSimulación completada. Resultados guardados en ens_eventos.csv")
