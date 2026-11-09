"""Método de Jacobi: solo el cálculo de A·x = b (sin interfaz)."""

import time

LIMITE_DIVERGENCIA = 1e12  # error (%) a partir del cual se considera que diverge


def jacobi(A, b, x0, tol, max_iter):
    """Resuelve A·x = b. Cada x_i nuevo usa solo valores de la iteración anterior.

    tol es el error relativo aproximado máximo permitido, en %.
    Devuelve (historial [(k, x, error%)], convergió, tiempo_ms, motivo).
    """
    n = len(b)
    x = list(x0)
    hist, conv, motivo = [], False, "No alcanzó el error permitido en el máximo de iteraciones"
    t0 = time.perf_counter()
    for k in range(1, max_iter + 1):
        nuevo = [
            (b[i] - sum(A[i][j] * x[j] for j in range(n) if j != i)) / A[i][i]
            for i in range(n)
        ]
        err = max(
            abs(nuevo[i] - x[i]) / abs(nuevo[i]) * 100 if nuevo[i] else abs(nuevo[i] - x[i]) * 100
            for i in range(n)
        )
        x = nuevo
        hist.append((k, list(x), err))
        if err != err or err > LIMITE_DIVERGENCIA:
            motivo = "Las iteraciones se alejan de la solución (diverge)"
            break
        if err < tol:
            conv, motivo = True, "Convergió"
            break
    return hist, conv, (time.perf_counter() - t0) * 1000, motivo
