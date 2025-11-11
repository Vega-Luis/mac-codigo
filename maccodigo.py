import sys
from explorador import ExploradorMacCodigo
from analizador import AnalizadorMacCodigo
from verificador.verificador import VerificadorSemantico
from calorimetro import MacCalorimetro


def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Error: faltan argumentos")
        print("Uso: python maccodigo.py <archivo_fuente.jama>")
        sys.exit(1)

    # Leer archivo fuente
    archivo_fuente = sys.argv[1]
    with open(archivo_fuente, encoding="utf-8") as f:
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
    else:
        print(" Verificación semántica completada sin errores.")

    # =============================================================
    # 4️⃣ ANÁLISIS DE COMPLEJIDAD
    # =============================================================
    print("\n=== ANÁLISIS DE COMPLEJIDAD ===")
    calorimetro = MacCalorimetro()
    calorimetro.medir(analizador.asa.raiz)
    calorimetro.imprimir_resumen()


if __name__ == "__main__":
    main()
