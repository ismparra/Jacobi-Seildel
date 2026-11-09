"""Lógica del circuito: validación de datos, sistema de Kirchhoff y ejecución de métodos."""

import re

from gauss_seidel import gauss_seidel
from jacobi import jacobi

METODOS = {"Jacobi": jacobi, "Gauss-Seidel": gauss_seidel}


def parsear_suma(texto):
    """'4 + 3, 2' -> 9.0 (resistencias propias de una malla)."""
    return sum(float(p) for p in re.split(r"[,+]", texto) if p.strip())


def leer_datos(mallas, compartidas, error, max_iter, x0):
    """Valida los textos capturados. mallas=[(V, Rpropias)], compartidas=[(a, b, R)].

    Devuelve (fuentes, propias, comp, tol, max_iter, x0); lanza ValueError con mensaje de usuario.
    """
    n = len(mallas)
    if n < 2:
        raise ValueError("Agregue al menos 2 mallas.")
    try:
        fuentes = [float(v) for v, _ in mallas]
        propias = [parsear_suma(r) for _, r in mallas]
        comp = [(int(a) - 1, int(b) - 1, float(r)) for a, b, r in compartidas]
        tol = float(error or 0.001)
        max_iter = int(max_iter or 100)
        x0 = [float(t) for t in x0.split(",")] if x0.strip() else [0.0] * n
    except ValueError:
        raise ValueError("Hay valores no numéricos o vacíos en los datos.")
    for a, b, _ in comp:
        if a == b or not (0 <= a < n and 0 <= b < n):
            raise ValueError(f"Resistencia compartida inválida: mallas {a + 1} y {b + 1}.")
    if len(x0) != n:
        raise ValueError(f"La aproximación inicial debe tener {n} valores (uno por malla).")
    if min(propias) < 0 or any(r < 0 for _, _, r in comp) or tol <= 0 or max_iter < 1:
        raise ValueError("Resistencias ≥ 0, error > 0 e iteraciones ≥ 1.")
    return fuentes, propias, comp, tol, max_iter, x0


def generar_sistema(fuentes, propias, compartidas):
    """Mallas (LVK): R_ii·I_i − Σ R_ij·I_j = V_i. compartidas=[(a, b, R)] con a, b base 0."""
    n = len(fuentes)
    A = [[0.0] * n for _ in range(n)]
    for i in range(n):
        A[i][i] = propias[i]
    for a, b, r in compartidas:
        A[a][a] += r
        A[b][b] += r
        A[a][b] -= r
        A[b][a] -= r
    return A, list(fuentes)


def ecuaciones_texto(A, b):
    eqs = []
    for i, fila in enumerate(A):
        t = ""
        for j, a in enumerate(fila):
            if a == 0:
                continue
            t += f" {'-' if a < 0 else '+'} " if t else ("-" if a < 0 else "")
            t += f"{abs(a):g}·I{j + 1}"
        eqs.append(f"Malla {i + 1}:  {t or '0'} = {b[i]:g}")
    return eqs


def es_diagonal_dominante(A):
    return all(abs(A[i][i]) >= sum(abs(a) for j, a in enumerate(A[i]) if j != i) for i in range(len(A)))


def ejecutar(metodo, A, b, x0, tol, max_iter):
    """metodo: 'Jacobi', 'Gauss-Seidel' o 'Ambos'. Devuelve {nombre: (hist, conv, ms, motivo)}."""
    return {n: f(A, b, x0, tol, max_iter) for n, f in METODOS.items() if metodo in (n, "Ambos")}


def veredicto(corridas):
    """Texto de comparación para el modo Ambos."""
    (hj, cj, tj, _), (hg, cg, tg, _) = corridas["Jacobi"], corridas["Gauss-Seidel"]
    if not (cj and cg):
        return "No se puede comparar: al menos un método no convergió."
    por_iter = "Empate" if len(hj) == len(hg) else "Jacobi" if len(hj) < len(hg) else "Gauss-Seidel"
    por_tiempo = "Jacobi" if tj < tg else "Gauss-Seidel"
    if por_iter == por_tiempo:
        return f"Más eficiente: {por_iter} (menos iteraciones y menor tiempo)"
    if por_iter == "Empate":
        return f"Mismas iteraciones; menor tiempo: {por_tiempo}"
    return f"Resultado mixto: menos iteraciones {por_iter}, menor tiempo {por_tiempo}"
