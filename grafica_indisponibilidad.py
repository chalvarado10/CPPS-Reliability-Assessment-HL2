import numpy as np
import matplotlib.pyplot as plt

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

# Tiempo: horas del año
t = np.arange(0, 24*365)

for componente in tasa_falla.keys():

    valores_falla = tasa_falla[componente]
    valores_rest = tasa_restauracion[componente]

    n = len(valores_falla)

    fig, axes = plt.subplots(
        n, 1,
        figsize=(12, 2.8*n),
        sharex=True,
        constrained_layout=True
    )

    if n == 1:
        axes = [axes]

    for i in range(n):

        lam = valores_falla[i]
        mu = valores_rest[i]

        indisponibilidad = (lam / (lam + mu))*100
        disponibilidad = (100 - indisponibilidad)

        y_indisp = np.full(len(t), indisponibilidad)
        y_disp = np.full(len(t), disponibilidad)

        axes[i].plot(t, y_disp, label=f"Disponibilidad A = {disponibilidad:.6f}")
        axes[i].plot(t, y_indisp, label=f"Indisponibilidad U = {indisponibilidad:.6f}", linestyle="--")

        axes[i].set_title(f"{componente[::].capitalize()} {i+1}")
        axes[i].set_ylabel("%")
        axes[i].set_xlim(0, 8760)
        axes[i].grid(True)
        axes[i].legend(loc="center right")

    axes[-1].set_xlabel("Tiempo [horas]")

    fig.suptitle(
        f"{componente.capitalize()} - Disponibilidad e Indisponibilidad",
        fontsize=14
    )
    plt.savefig(f"{componente}_disponibilidad_indisponibilidad.png", dpi=600)
    plt.show()
    