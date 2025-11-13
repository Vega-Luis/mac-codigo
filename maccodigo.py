from __future__ import annotations

import argparse
import sys
from pathlib import Path

from explorador import ExploradorMacCodigo
from analizador import AnalizadorMacCodigo
from verificador.verificador import VerificadorSemantico
from generador import GeneradorCodigoPython

from calorimetro import MacCalorimetro


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta el compilador de MacCódigo y, opcionalmente, emite el "
            "código Python equivalente generado a partir del ASA."
        )
    )
    parser.add_argument("archivo_fuente", help="Ruta al archivo fuente en MacCódigo (.jama)")
    parser.add_argument(
        "--emit-python",
        "-o",
        metavar="ARCHIVO",
        help="Escribe el código Python generado en el archivo indicado.",
    )
    parser.add_argument(
        "--mostrar-python",
        action="store_true",
        help="Muestra el código Python generado en la salida estándar.",
    )

    args = parser.parse_args()

    with open(args.archivo_fuente, encoding="utf-8") as f:
        codigo_fuente = f.read()

    # =============================================================
    # 1️⃣ ANÁLISIS LÉXICO
    # =============================================================
    print("=== ANÁLISIS LÉXICO ===")
    explorador = ExploradorMacCodigo(codigo_fuente)
    componentes = explorador.explorar()
    explorador.imprimir_componentes()
    explorador.imprimir_errores()

    # =============================================================
    # 2️⃣ ANÁLISIS SINTÁCTICO
    # =============================================================
    print("\n=== ANÁLISIS SINTÁCTICO ===")
    analizador = AnalizadorMacCodigo(componentes)
    try:
        analizador.analizar()
        print(" Análisis sintáctico completado correctamente.")
    except Exception as e:
        print(f" Error sintáctico: {e}")
        sys.exit(1)

    print("\n=== ÁRBOL DE SINTAXIS ABSTRACTA ===")
    analizador.asa.imprimir()

    # =============================================================
    # 3️⃣ VERIFICACIÓN SEMÁNTICA
    # =============================================================
    print("\n=== VERIFICACIÓN SEMÁNTICA ===")
    verificador = VerificadorSemantico(analizador.asa, verbose=True)
    errores = verificador.verificar()

    if errores:
        print("\n".join(errores))
        sys.exit(1)

    print(" Verificación semántica completada sin errores.")

    # =============================================================
    # 4️⃣ GENERACIÓN DE CÓDIGO PYTHON
    # =============================================================
    if args.emit_python or args.mostrar_python:
        generador = GeneradorCodigoPython(analizador.asa)
        codigo_python = generador.generar()

        if args.mostrar_python:
            print("\n=== CÓDIGO PYTHON GENERADO ===")
            print(codigo_python)

        if args.emit_python:
            ruta_destino = Path(args.emit_python)
            ruta_destino.write_text(codigo_python, encoding="utf-8")
            print(f"\n Código Python escrito en {ruta_destino.resolve()}")

    # =============================================================
    # 5️⃣ ANÁLISIS DE COMPLEJIDAD
    # =============================================================
    print("\n=== ANÁLISIS DE COMPLEJIDAD ===")
    calorimetro = MacCalorimetro()
    calorimetro.medir(analizador.asa.raiz)
    calorimetro.imprimir_resumen()


if __name__ == "__main__":
    main()
