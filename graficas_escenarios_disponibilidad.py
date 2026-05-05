import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
t = np.arange(0, 24*365)

U_1 = np.full(len(t),21.65)
U_2 = np.full(len(t),18.98)
U_3 = np.full(len(t),20.50)

A_1= np.full(len(t),100-21.65)
A_2= np.full(len(t),100-18.98)
A_3= np.full(len(t),100-20.50)

plt.figure(figsize=(12, 6))
plt.plot(t, U_1, label="U", linestyle='--', color='red')
plt.plot(t, A_1, label="A", color='blue')
plt.xlabel("Tiempo [horas]")
plt.ylabel("Porcentaje (%)")
plt.title("Escenario 1 - Disponibilidad e Indisponibilidad", fontsize=14)
plt.xlim(0, 8760)
plt.ylim(0, 100)
plt.legend(loc='best')
plt.show()
plt.savefig("escenario_1_disponibilidad_indisponibilidad.png", dpi=600)

plt.figure(figsize=(12, 6))
plt.plot(t, U_3, label="U", linestyle='--', color='red')
plt.plot(t, A_3, label="A", color='blue')
plt.xlabel("Tiempo [horas]")
plt.ylabel("Porcentaje (%)")
plt.title("Escenario 3 - Disponibilidad e Indisponibilidad", fontsize=14)
plt.xlim(0, 8760)
plt.ylim(0, 100)
plt.legend(loc='best')
plt.show()
plt.savefig("escenario_3_disponibilidad_indisponibilidad.png", dpi=600)

plt.figure(figsize=(12, 6))
plt.plot(t, U_2, label="U", linestyle='--', color='red')
plt.plot(t, A_2, label="A", color='blue')
plt.xlabel("Tiempo [horas]")
plt.ylabel("Porcentaje (%)")
plt.title("Escenario 2 - Disponibilidad e Indisponibilidad", fontsize=14)
plt.xlim(0, 8760)
plt.ylim(0, 100)
plt.legend(loc='best')
plt.show()
plt.savefig("escenario_2_disponibilidad_indisponibilidad.png", dpi=600)

