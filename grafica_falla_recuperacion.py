import numpy as np
import matplotlib.pyplot as plt

import numpy as np
import matplotlib.pyplot as plt

# Datos
tasa_falla = {
    "lineas": [1/4380, 1/4115, 1/4511, 1/4320, 1/4000, 1/3945],
    "transformadores": [1/4150, 1/4380, 1/4122],
    "generadores": [1/1752, 1/1740, 1/2190],
}

tasa_restauracion = {
    "lineas": [1/5, 1/4, 1/3, 1/6, 1/4, 1/5],
    "transformadores": [1/4, 1/3, 1/35],
    "generadores": [1/120, 1/100, 1/150],
}

# Tiempo (horas del año)
t = np.arange(0, 24*365)

for componente in tasa_falla.keys():

    valores_falla = tasa_falla[componente]
    valores_rest = tasa_restauracion[componente]

    n = len(valores_falla)

    fig, axes = plt.subplots(n, 1, figsize=(12, 2.5*n), sharex=True)

    if n == 1:
        axes = [axes]

    for i in range(n):

        y_falla = np.full(len(t), valores_falla[i])
        y_rest = np.full(len(t), valores_rest[i])

        axes[i].plot(t, y_falla, label="λ (falla)", linestyle='--')
        axes[i].plot(t, y_rest, label="μ (restauración)")

        axes[i].set_title(f"{componente[:-2].capitalize()} {i+1}")
        axes[i].set_ylabel("1/h")
        axes[i].grid(True)
        axes[i].legend()

    axes[-1].set_xlabel("Tiempo [horas]")
    plt.suptitle(f"{componente.capitalize()} - Tasa de Falla y Restauración", fontsize=14)

    plt.xlim(0, 8760)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(f"{componente}_tasa_falla_restauracion.png", dpi=600)
    plt.show()