import sys
import numpy as np
import pandas as pd
import random
from scipy.stats.qmc import LatinHypercube
import normalizar_carga as nc
import tasa_falla_scada as ts

# Definimos la ruta de PowerFactory

PFD_path = r"C:\Program Files\DIgSILENT\PowerFactory 2022\Python\3.10"
sys.path.append(PFD_path)
import powerfactory as pf  # Importamos la libreria de PowerFactory

# Inicializamos la aplicación de PowerFactory
app = pf.GetApplication()  # Se crea instanacia en Digsilent
if app is None:
    raise EnvironmentError("PowerFactory no está abierto o no se puede acceder desde Python.")

app.ClearOutputWindow()  # Limpiamos la ventana de salida
app.Show()  # Mostramos la aplicación
prj = app.ActivateProject("Nine-bus System")
ldf = app.GetFromStudyCase("ComLdf")

# Obtenemos el perfil de carga normalizado
df = pd.read_csv(r"C:\Users\ASUS\OneDrive\Tesis\Tesis Espol\loadprofile_horaria.csv", sep =',',names = ['hora', 'kW'])
# Normalizamos el perfil de carga
df_nor = nc.normalizar_carga(df)
df_normalizado = df_nor["pu"]
print(df_normalizado)

# Obtenemos componentes del sistema de potencia:
"""Obtenemos las líneas, transformadores y generadores del sistema de potencia, para luego almacenarlas en un diccionario"""
lineas = app.GetCalcRelevantObjects("*.ElmLne")
trafo = app.GetCalcRelevantObjects("*.ElmTr2")
generadores = app.GetCalcRelevantObjects("*.ElmSym")
cargas = app.GetCalcRelevantObjects("*.Elmlod")
barras = app.GetCalcRelevantObjects("*.ElmTerm")
scada = app.GetCalcRelevantObjects("*.ElmLne")
#Definimos el tiempo de estudio en horas
t_estudio = 8760 # Tiempo de estudio en horas (365 días) 

# Definimos los valores de cada carga del sistema para este caso 3

load_1 = cargas[0].GetAttribute("plini")
load_2 = cargas[1].GetAttribute("plini")
load_3 = cargas[2].GetAttribute("plini")

loads = [load_1, load_2, load_3]

componentes = {
    "lineas": lineas,
    "transformadores": trafo,
    "generadores": generadores,
    "scada": scada,
}

# Definimos tasas de falla y restauración para cada componente por hora
p_ied, n_ied, p_switch, n_switch, p_server, n_server, p_cl, n_cl = [(168000/(48+168000)), 5, (438000/(48+438000)), 1, (125000/(48+125000)), 1, (11750000/(48+11750000)), 1]

df = ts.tasa_falla_scada(p_ied, n_ied, p_switch, n_switch, p_server, n_server, p_cl, n_cl)

tasa_falla = {
    "lineas": [1/4380, 1/4115, 1/4511, 1/4320, 1/4000, 1/3945],
    "transformadores":[1/4150, 1/4380, 1/4122],
    "generadores": [1/1752, 1/1740, 1/2190],
    "scada": [float(df[2])]*max(1,len(scada))
   
}
tasa_restauracion = {
    "lineas": [1/5, 1/4, 1/3, 1/6, 1/4, 1/5],
    "transformadores": [1/4, 1/3, 1/35],
    "generadores": [1/120, 1/100, 1/150],
    "scada": [float(df[1])]*max(1,len(scada))
}

n_eventos = 200

tasa_por_evento = []  # Lista para almacenar las tasas por evento
for i in range(n_eventos):
    resultados_fallas = []  # Lista para almacenar los resultados de las fallas
    for tipo, lista in componentes.items():
        lam_list = tasa_falla[tipo]
        mu_list = tasa_restauracion[tipo]
        lhs = LatinHypercube(d=2).random(len(lista))
        lhs = np.clip(lhs, 1e-6, 1)  # Aseguramos que las muestras estén en el rango [0, 1]
        for j, obj in enumerate(lista):
            u,v = lhs[j]
            lam = float(lam_list[j])
            mu = float(mu_list[j])
            tf = float(-np.log(u)/lam)
            tr = float(-np.log(v)/mu)
            resultados_fallas.append((tf, lam, tipo, obj, tr))
    tasa_por_evento.append(resultados_fallas)

hdownsystem = np.zeros(n_eventos) # Lista para almacenar tiempos de caída del sistema
LC = np.zeros(n_eventos); # Corte de carga en MW
VR = np.zeros(n_eventos, dtype=int) # Veces que se aplica el corte de carga

hdownsystem_avr_1 = []  # Lista para almacenar tiempos promedio de caída del sistema por evento
hdsystem = []  # Lista para almacenar el tiempo promedio de caída del sistema
# Iteramos sobre el número de eventos para simular la falla y reparación de los componentes

for e in range(n_eventos):
    
    t = 0 #inicializamos tiempo acumulado
    VR[e] = 0 # Inicializamos las veces que se aplica el corte de carga
    LC[e] = 0 # Inicializamos el corte de carga en MW
    hdownsystem[e] = 0 # Inicializamos el tiempo de caída del sistema
    hora = random.randint(0,len(df_normalizado)-1)  # Seleccionamos una hora aleatoria del perfil de carga
    carga_pu = df_normalizado[hora]
    #Realizamos la variación aleatoria de carga para el evento actual
    for carga in cargas:
        carga.SetAttribute("plini", carga_pu* carga.GetAttribute("plini"))
    
    print(f"Evento {e+1}/{n_eventos}")  # Imprimimos el número del evento actual
    elemento_fallado = tasa_por_evento[e]  # Obtenemos los resultados de fallas del evento actual
    
    
    while t < t_estudio:  # Simulamos hasta tiempo de estudio 

        # Calculamos el tiempo de falla y el tiempo de reparación de cada componente
        componente_falla_primero = min(elemento_fallado, key=lambda x: x[0])
        tf_min, tasa_falla_min, tipo_min, obj_min, tr_min = componente_falla_primero
        t+= tf_min  # Actualizamos el tiempo acumulado
        print(t)
        if t > t_estudio:  # Si el tiempo acumulado supera las 24 horas, salimos del bucle
            break
        
        obj_fallado = obj_min
        
        print(obj_fallado)

        carga_fallado_1 = cargas[0] 
        carga_fallado_2 = cargas[1]
        carga_fallado_3 = cargas[2] 

        obj_fallado.outserv = 1  # Activamos el observador de fallos

        ldf.Execute(iopt_net=2)  # Ejecutamos el flujo de carga
        carga_tot = 0;

        paso_1 = 0;
        paso_2 = 0;
        paso_3 = 0;

        for i in range(4):

            if i ==0 & paso_1 == 0:
                for lin in lineas:
                    if lin == obj_fallado:
                        continue  # Saltamos la línea que ha fallado
                    else:
                        cargabilidad = lin.GetAttribute("c:loading")
                        if cargabilidad <= lin.GetAttribute("maxload"):
                            print("linea ok")
                        else:
                            paso_1 += 1
                            print("linea sobrecargada")
                for bus in barras:
                    conectados = bus.GetConnectedElements()  # Obtenemos los elementos conectados a cada barra
                    for i in conectados:
                        if i.GetClassName() == "ElmSym":
                            for gen in generadores:
                                if gen == obj_fallado:
                                    continue
                                else:
                                    if i.loc_name == gen.loc_name:
                                        if bus.GetAttribute("m:Pgen") < i.GetAttribute("Pnom"):
                                            print("generador ok")
                                        else:
                                            paso_1 += 1
                                            print("generador sobrecargado")
                if paso_1 == 0:
                    print("No hay sobrecargas")
                    break
            
            elif (i==1) & (paso_1 > 0):
                print(f"Desconectamos primer paso de carga:{carga_fallado_1.loc_name}")
                carga_fallado_1.outserv = 1  # Desactivamos el observador de fallos
                VR[e]+=1
                LC[e]+=(carga_fallado_1.GetAttribute("plini")*tr_min)
                
                ldf.Execute(iopt_net=2)  # Ejecutamos el flujo de carga
                for lin in lineas:
                        if lin == obj_fallado:
                            continue  # Saltamos la línea que ha fallado
                        else:
                            cargabilidad = lin.GetAttribute("c:loading")
                            if cargabilidad <= lin.GetAttribute("maxload"):
                                print("linea ok")
                            else:
                                paso_2 += 1
                                print("linea sobrecargada")                                  
                for bus in barras:
                    conectados = bus.GetConnectedElements()  # Obtenemos los elementos conectados a cada barra
                    for i in conectados:
                        if i.GetClassName() == "ElmSym":
                            for gen in generadores:
                                if gen == obj_fallado:
                                    continue
                                else:
                                    if i.loc_name == gen.loc_name:
                                        if bus.GetAttribute("m:Pgen") < i.GetAttribute("Pnom"):
                                            print("generador ok")
                                        else:
                                            paso_2 += 1
                                            print("generador sobrecargado")

                carga_fallado_1.outserv = 0  # Reactivamos el observador de fallos    
                if paso_2 == 0:
                    print("No hay sobrecargas")
                    break
            elif (i==2) & (paso_2 > 0):
                print(f"Desconectamos segundo paso de carga:{carga_fallado_1.loc_name} y {carga_fallado_2.loc_name}")
                carga_fallado_1.outserv = 1  # Desconectamos carga
                carga_fallado_2.outserv = 1 # Desconectamos carga
                VR[e]+=1
                LC[e]+=((carga_fallado_1.GetAttribute("plini")+carga_fallado_2.GetAttribute("plini"))*tr_min)
                ldf.Execute(iopt_net=2)  # Ejecutamos el flujo de carga
                for lin in lineas:
                        if lin == obj_fallado:
                            continue  # Saltamos la línea que ha fallado
                        else:
                            cargabilidad = lin.GetAttribute("c:loading")
                            if cargabilidad <= lin.GetAttribute("maxload"):
                                print("linea ok")
                            else:
                                paso_3 += 1
                                print("linea sobrecargada")
                                
                for bus in barras:
                    conectados = bus.GetConnectedElements()  # Obtenemos los elementos conectados a cada barra
                    for i in conectados:
                        if i.GetClassName() == "ElmSym":
                            for gen in generadores:
                                if gen == obj_fallado:
                                    continue
                                else:
                                    if i.loc_name == gen.loc_name:
                                        if bus.GetAttribute("m:Pgen") < i.GetAttribute("Pnom"):
                                            print("generador ok")
                                        else:
                                            paso_3 += 1
                                            print("generador sobrecargado")
                                            
                carga_fallado_1.outserv = 0  # Reactivamos el observador de fallos
                carga_fallado_2.outserv = 0 # Reactivamos el observador de fallos
                if paso_3 ==0:
                    print("No hay sobrecargas")
                    break
            elif (i==3) & (paso_3 > 0):
                print(f"Desconectamos toda la carga:{carga_fallado_1.loc_name}, {carga_fallado_2.loc_name}, {carga_fallado_3.loc_name}")
                carga_fallado_1.outserv = 1
                carga_fallado_2.outserv = 1
                carga_fallado_3.outserv = 1
                print("Desconecta toda la carga")
                VR[e]+=1
                LC[e]+=((carga_fallado_1.GetAttribute("plini")+carga_fallado_2.GetAttribute("plini")+carga_fallado_3.GetAttribute("plini"))*tr_min)
                # ldf.Execute(iopt_net=2)
                carga_fallado_1.outserv = 0
                carga_fallado_2.outserv = 0
                carga_fallado_3.outserv = 0
                
        print(paso_1)
        print(paso_2)
        print(paso_3)
        print(e)

        obj_fallado.outserv = 0  # Activamos el observador de fallos
                
        hdownsystem[e]+=(tr_min)  # Almacenamos el tiempo de caída del sistema
        t+= tr_min  # Sumamos el tiempo de reparación
        
        print(t)
        
        if t > t_estudio:  # Si el tiempo acumulado supera las 24 horas, salimos del bucle
            break

    hdownsystem_avr_1.append(hdownsystem[e])  # Almacenamos el tiempo de caída del sistema por evento
    hdsystem.append(np.mean(hdownsystem_avr_1))  # Calculamos el tiempo promedio de caída del sistema por evento
    
    cargas[0].SetAttribute("plini", load_1)  # Restauramos el valor original de la carga
    cargas[1].SetAttribute("plini", load_2)  # Restauramos el valor original de la carga
    cargas[2].SetAttribute("plini", load_3)  # Restauramos el valor original de la carga

    
hdownsystem_avr = np.mean(hdownsystem)  # Calculamos el tiempo promedio de caída del sistema

ELC = np.mean(LC)  # Calculamos el corte de carga promedio
ENLC = round(np.mean(VR)) #[falla/año] # Calculamos las veces que se aplica el corte de carga promedio
PLC = ((hdownsystem_avr / t_estudio)) * 100  # Calculamos la indisponibilidad en porcentaje
EDLC = (PLC/100)*t_estudio #[horas/año]
ADLC = (EDLC/ENLC) # [hora/disturbio]
print(f"Probabilidad de Corte de Carga: {PLC:.2f}%")
print(f"Tiempo promedio de caída del sistema: {hdownsystem_avr:.2f} horas")
print(f"Energía no suplida por el corte de carga: {ELC:.2f} MWh/tiempo de estudio")
print(f"Número esperado de cortes de carga: {ENLC:.2f} [falla/periodo de estudio]")
print(f"Duración Esperada del Corte de Carga: {EDLC:.2f} [periodo/tiempo de estudio]")
print(f"Duración Media de las Reducciones de Carga: {ADLC:.2f} [tiempo/falla]")
print(VR)
print(hdownsystem)
# Graficamos los resultados para cada evento de hdownsystem
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.plot(range(1, n_eventos + 1), hdsystem, label ='Hdownsystem', linestyle='-', color='b')
plt.xlabel('Número de Evento')
plt.ylabel('Tiempo de caída del sistema (horas)')
plt.title('Tiempo de caída del sistema por evento')
plt.grid() 
plt.show()  # Mostramos la gráfica