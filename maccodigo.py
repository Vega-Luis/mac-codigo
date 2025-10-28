import sys
from explorador import ExploradorMacCodigo
from analizador import AnalizadorMacCodigo


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

    print("=== ANÁLISIS LÉXICO ===")
    explorardor = ExploradorMacCodigo(codigo_fuente)
    componentes = explorardor.explorar()
    explorardor.imprimir_componentes()
    explorardor.imprimir_errores()

    print("\n=== ANÁLISIS SINTÁCTICO ===")
    analizador = AnalizadorMacCodigo(componentes)
    analizador.analizar()
    print("\n=== ÁRBOL DE SINTAXIS ABSTRACTA ===")
    analizador.asa.imprimir()


if __name__ == "__main__":
    main()
