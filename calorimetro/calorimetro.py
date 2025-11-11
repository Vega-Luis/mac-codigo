
from utils.arbol import TipoNodo


class MacCalorimetro:
    """
    Calcula la "complejidad calórica" del código analizado,
    asignando un peso calórico a cada tipo de nodo en el AST.
    """

    COSTO_CALORICO = {
        TipoNodo.PROGRAMA: 0,
        TipoNodo.ASIGNACION: 1,
        TipoNodo.CONDICIONAL: 2,
        TipoNodo.REPETICION: 5,
        TipoNodo.FUNCION: 2,
        TipoNodo.BLOQUE_INSTRUCCIONES: 0,
        TipoNodo.EXPRESION: 1,
        TipoNodo.CONDICION: 1,
        TipoNodo.COMPARADOR: 1,
        TipoNodo.OPERADOR: 1,
        TipoNodo.ENTERO: 0,
        TipoNodo.FLOTANTE: 0,
        TipoNodo.STRING: 0,
        TipoNodo.BOOLEANO: 0,
        TipoNodo.CARACTER: 0,
        TipoNodo.IDENTIFICADOR: 0,
        TipoNodo.DECLARACION_VARIABLE: 1,
        TipoNodo.DECLARACION: 1,
        TipoNodo.PARAMETROS: 0,
        TipoNodo.SECCION_CODIGO: 0,
        TipoNodo.INVOCACION: 2,
        TipoNodo.INDEXACION: 1,
        TipoNodo.TERMINO: 0,
        TipoNodo.RETORNO: 1,
        TipoNodo.SIS: 1,
        TipoNodo.DECLARACION_FUNCION: 2,
        TipoNodo.SECCION_DECLARACIONES: 0,
        TipoNodo.BLOQUE_DECLARACION_VARIABLE: 0,
        TipoNodo.TIPO_DATO: 0,
        TipoNodo.LITERAL_COMPUESTO: 1,
    }

    def __init__(self):
        self.total_calorias = 0
        self.detalle = []
        self.max_profundidad_bucle = 0

    def medir(self, nodo, profundidad_bucle=0):
        """
        Mide las calorías del nodo dado y sus hijos recursivamente.
        """
        if nodo is None:
            return 0

        tipo = getattr(nodo, "tipo", None)
        peso = self.COSTO_CALORICO.get(tipo, 0)

        if tipo == TipoNodo.REPETICION:
            profundidad_bucle += 1
            self.max_profundidad_bucle = max(
                self.max_profundidad_bucle,
                profundidad_bucle
            )

        if tipo == TipoNodo.CONDICIONAL and profundidad_bucle > 0:
            peso *= 1.5

        self.total_calorias += peso

        nombre = tipo.name if hasattr(tipo, "name") else str(tipo)
        contenido = f" ({nodo.contenido})" if getattr(nodo, "contenido", None) else ""
        self.detalle.append(f"{nombre}{contenido} → {peso}")

        for hijo in getattr(nodo, "nodos", []) or []:
            self.medir(hijo, profundidad_bucle)

        return self.total_calorias

    def imprimir_resumen(self):
        """
        Imprime el resumen del análisis calórico.
        """

        print("Conteo de calorías")
        for linea in self.detalle:
            print(linea)
        print("--------------------")
        print(f"Total exacto = {self.total_calorias} calorías")
        print(f"Profundidad máxima de bucle = {self.max_profundidad_bucle}")
        print(f"Complejidad total: {self.calcular_complejidad()}")

    def calcular_complejidad(self):
        """
        Traduce el nivel de anidamiento en una clase Big-O realista.
        """

        if self.max_profundidad_bucle == 0:
            return "O(1)"
        elif self.max_profundidad_bucle == 1:
            return "O(n)"
        else:
            return f"O(n^{self.max_profundidad_bucle})"
