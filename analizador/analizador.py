from explorador.explorador import TipoComponente
from utils.arbol import TipoNodo, NodoArbol, ArbolSintaxisAbstracta


class AnalizadorMacCodigo:
    """
    Analizador sintáctico para el lenguaje MacCódigo.

    Construye un árbol de sintaxis abstracta (ASA) siguiendo la gramática
    del lenguaje.

    Parámetros
    ----------
    lista_componentes : list
        Lista de componentes léxicos generados por el explorador léxico.

    Atributos
    ----------
    componentes_lexicos : list
        Lista de componentes léxicos a analizar.
    cantidad : int
        Cantidad total de componentes léxicos.
    posicion : int
        Posición actual en la lista de componentes léxicos.
    componente_actual : ComponenteLexico
        Componente léxico actualmente analizado.
    asa : ArbolSintaxisAbstracta
        Árbol de sintaxis abstracta generado a partir del análisis.
    """

    def __init__(self, lista_componentes: list):
        self.componentes_lexicos = lista_componentes
        self.cantidad = len(lista_componentes)
        self.posicion = 0
        self.componente_actual = (
            lista_componentes[0]
            if lista_componentes
            else None
        )
        self.asa = ArbolSintaxisAbstracta()
        self.errores = []

    def analizar(self):
        """
        Inicia el análisis sintáctico y construye el ASA.
        """
        self.asa.raiz = self.__analizar_programa()

    def __analizar_programa(self):
        """
        Analiza la estructura principal del programa.

        Programa ::=
            “hambriento” { Declaración } Sección_de_código “satisfecho”
        """
        nodos = []

        # Verificar inicio del programa
        self.verificar_token("hambriento")

        # { Declaración }
        nodos.append(self.analizar_declaracion())

        nodos.append(self.verificar_seccion_codigo())

        # Verificar fin del programa
        self.verificar_token("satisfecho")
        self.verificar_fin_archivo()  # Verificar que no haya más tokens

        return NodoArbol(TipoNodo.PROGRAMA, nodos=nodos)

    # === ASIGNACIÓN ===
    def analizar_asignacion(self):
        """
        Asignacion ::=
        Nombre_del_tipo Identificador <- (Literal | Expresion | Invocación)
        """
        nodos = []

        # Si hay un TIPO antes del identificador
        # (p.ej. 'torta id <- 101'), lo saltamos
        if (
            self.componente_actual is not None
            and self.componente_actual.tipo == TipoComponente.TIPO
        ):
            self.__siguiente()

        identificador = self.verificar_identificador()
        nodos.append(identificador)

        self.verificar_token("<-")

        # Literal simple
        if self.componente_actual.tipo in (
            TipoComponente.ENTERO,
            TipoComponente.FLOTANTE,
            TipoComponente.STRING,
            TipoComponente.BOOLEANO,
            TipoComponente.CARACTER,
        ):
            literal = self.analizar_literal()
            nodos.append(literal)


        # Expresión (identificadores, operadores, etc.)
        else:
            nodos.append(self.analizar_expresion())

        return NodoArbol(TipoNodo.ASIGNACION, nodos=nodos)

    def analizar_condicional(self):
        """
        Condicional ::=
            “¿si?” Comparación Bloque_de_instrucciones “¡de otro modo!”
        """
        nodos = []
        self.verificar_token("¿si?")
        nodos.append(self.analizar_condicion())
        nodos.append(self.verificar_bloque_instrucciones())
        self.verificar_token("¡de otro modo!")
        nodos.append(self.verificar_bloque_instrucciones())
        return NodoArbol(TipoNodo.CONDICIONAL, nodos=nodos)

    # === REPETICIÓN ===
    def analizar_repeticion(self):
        """
        Repeticion ::=  “para” Identificador “<-” Expresión “hasta”
            Bloque_de_instrucciones
        """
        nodos = []
        self.verificar_token("para")
        nodos.append(self.verificar_identificador())
        self.verificar_token("<-")
        nodos.append(self.analizar_literal())
        self.verificar_token("hasta")
        nodos.append(self.analizar_literal())
        nodos.append(self.verificar_bloque_instrucciones())
        return NodoArbol(TipoNodo.REPETICION, nodos=nodos)

    # === FUNCIÓN ===
    def analizar_funcion(self):
        """
        Funcion ::= receta Identificador (Parametros) { Instruccion* }
        """
        nodos = []
        self.verificar_token("receta")

        identificador = self.verificar_identificador()
        nodos.append(identificador)

        self.verificar_token("(")

        parametros = self.analizar_parametros_definicion()
        nodos.append(parametros)

        self.verificar_token(")")

        bloque = self.verificar_bloque_instrucciones()
        nodos.append(bloque)

        return NodoArbol(TipoNodo.FUNCION, nodos=nodos)

    # === INSTRUCCIONES ===
    def analizar_instruccion(self):
        """
        Instruccion
            ::= Condicional | Repeticion | Asignacion | Invocacion | Retorno
        """
        if self.componente_actual.texto == "¿si?":
            return self.analizar_condicional()
        elif self.componente_actual.texto == "para":
            return self.analizar_repeticion()
        elif self.componente_actual.tipo == TipoComponente.IDENTIFICADOR:
            return self.analizar_instruccion_identificador()
        elif self.componente_actual.tipo in [
            TipoComponente.TIPO
        ]:
            return self.analizar_asignacion()
        else:
            # ignorar separadores u otros tokens sueltos
            # self.__siguiente()
            return NodoArbol(TipoNodo.EXPRESION, contenido="")

    # === CONDICIONES / EXPRESIONES / LITERALES ===
    def analizar_condicion(self):
        """
        Condicion ::= Valor Comparador Valor
        """
        nodos = [self.analizar_valor()]
        self.verificar_tipo(TipoComponente.COMPARADOR)
        nodos.append(NodoArbol(
            TipoNodo.COMPARADOR,
            contenido=self.componente_actual.texto)
        )
        self.__siguiente()
        nodos.append(self.analizar_valor())

        return NodoArbol(TipoNodo.CONDICION, nodos=nodos)

    def analizar_expresion(self):
        """
        Expresion ::= Valor (Operador Valor)*
        """
        nodos = [self.analizar_valor()]
        while (
            self.componente_actual
            and self.componente_actual.tipo == TipoComponente.OPERADOR
        ):
            op = NodoArbol(
                TipoNodo.OPERADOR,
                contenido=self.componente_actual.texto
            )
            self.__siguiente()
            nodos.append(op)
            nodos.append(self.analizar_valor())
        return NodoArbol(TipoNodo.EXPRESION, nodos=nodos)

    def analizar_valor(self):
        if self.componente_actual.tipo == TipoComponente.IDENTIFICADOR:
            return self.verificar_identificador()
        elif self.componente_actual.tipo in (
            TipoComponente.ENTERO,
            TipoComponente.FLOTANTE,
            TipoComponente.STRING,
            TipoComponente.BOOLEANO,
            TipoComponente.CARACTER,
        ):
            return self.analizar_literal()
        else:
            raise Exception(
                f"Error de sintaxis: Se esperaba un identificador o un literal, "
                f"pero se encontró '{self.componente_actual.texto}'\n"
                f"--> línea {self.componente_actual.linea}, "
                f"columna {self.componente_actual.columna}."
            )

    def analizar_literal(self):
        tipo = self.componente_actual.tipo
        mapa = {
            TipoComponente.ENTERO: TipoNodo.ENTERO,
            TipoComponente.FLOTANTE: TipoNodo.FLOTANTE,
            TipoComponente.STRING: TipoNodo.STRING,
            TipoComponente.BOOLEANO: TipoNodo.BOOLEANO,
            TipoComponente.CARACTER: TipoNodo.CARACTER,
        }
        nodo = NodoArbol(
            mapa.get(tipo),
            contenido=self.componente_actual.texto
        )
        self.__siguiente()
        return nodo

    # === PARÁMETROS ===
    def analizar_parametros_definicion(self):
        """
        ParametrosDefinicion ::= Identificador (',' Identificador)*
        """
        nodos = []
        if self.componente_actual.texto == ")":
            return NodoArbol(TipoNodo.PARAMETROS, nodos=nodos)
        nodos.append(self.verificar_identificador())
        while self.componente_actual.texto == ",":
            self.__siguiente()
            nodos.append(self.verificar_identificador())
        return NodoArbol(TipoNodo.PARAMETROS, nodos=nodos)

    def analizar_instruccion_simple(self):
        """
        InstruccionSimple ::= PALABRA_CLAVE ( STRING | IDENTIFICADOR )*
        """
        palabra = self.componente_actual.texto
        nodo_principal = NodoArbol(TipoNodo.EXPRESION, contenido=palabra)
        self.__siguiente()

        # Captura argumentos entre paréntesis si existen
        if self.componente_actual and self.componente_actual.texto == "(":
            self.__siguiente()
            hijos = []
            while (
                self.componente_actual
                and self.componente_actual.texto != ")"
            ):
                if self.componente_actual.tipo in (
                    TipoComponente.STRING,
                    TipoComponente.IDENTIFICADOR,
                    TipoComponente.ENTERO,
                    TipoComponente.FLOTANTE,
                ):
                    hijos.append(self.analizar_valor())
                else:
                    self.__siguiente()
            nodo_principal.nodos = hijos
            if self.componente_actual and self.componente_actual.texto == ")":
                self.__siguiente()

        return nodo_principal

    def verificar_tipo(self, tipo):
        if self.componente_actual and self.componente_actual.tipo != tipo:
            raise Exception(
                f"Error de sintaxis: Se esperaba tipo '{tipo}', "
                f"pero se encontró '{self.componente_actual.tipo}'\n"
                f"--> línea {self.componente_actual.linea},"
                f"columna {self.componente_actual.columna}."
            )

    def verificar_identificador(self):
        if self.componente_actual.tipo not in [
            TipoComponente.IDENTIFICADOR,
            TipoComponente.TIPO
        ]:
            raise Exception(
                f"Error de sintaxis: Se esperaba un  tipo, "
                f"se encontró '{self.componente_actual.texto}'\n"
                f"--> línea {self.componente_actual.linea}, "
                f"columna {self.componente_actual.columna}")
        nodo = NodoArbol(
            TipoNodo.IDENTIFICADOR,
            contenido=self.componente_actual.texto
        )
        self.__siguiente()
        return nodo

    def __siguiente(self):
        self.posicion += 1
        if self.posicion < self.cantidad:
            self.componente_actual = self.componentes_lexicos[self.posicion]
        else:
            self.componente_actual = None

    def analizar_declaracion_variable(self):
        """
        Analiza una declaración de variable.

        Declaración_de_variable ::=
            “ingrediente” Asignación { “,” Asignación } “.”
        """
        nodos = []
        if self.componente_actual.texto != "ingrediente":
            raise Exception(
                f"Se esperaba la palabra reservada'ingrediente',"
                f"pero se encontró '{self.componente_actual.texto}',"
                f"línea {self.componente_actual.linea},"
                f"columna {self.componente_actual.columna}."
            )
        self.__siguiente()

        while self.componente_actual and self.componente_actual.texto != ".":
            asignacion = self.analizar_asignacion()
            # Agregar la asignación al nodo de declaración
            nodos.append(asignacion)
            if self.componente_actual and self.componente_actual.texto == ",":
                self.__siguiente()  # Saltar la coma
        self.verificar_token(".")
        return NodoArbol(TipoNodo.DECLARACION_VARIABLE, nodos=nodos)

    def verificar_fin_archivo(self):
        """
        Verifica que se haya llegado al final del archivo después de 'satisfecho'.
        Si no es así, lanza una excepción indicando el error.
        """
        if self.componente_actual is not None:
            raise Exception(
                f"Error de sintaxis: "
                f"se esperaba el fin del archivo después de 'satisfecho', "
                f"pero se encontró "
                f"'{self.componente_actual.texto}'\n"
                f"--> línea {self.componente_actual.linea}, "
                f"columna {self.componente_actual.columna}"
            )

    def verificar_seccion_codigo(self):
        """
        Verifica que la sección de código
        esté presente después de las declaraciones.
        Si no es así, lanza una excepción indicando el error.
        """
        nodos = []
        self.verificar_token("cocinar")
        nodos.append(self.verificar_bloque_instrucciones())
        return NodoArbol(
            TipoNodo.SECCION_CODIGO,
            contenido="cocinar", nodos=nodos
        )

    def analizar_declaracion(self):
        """
        Analiza una declaración antes de la sección de código.

        Declaración ::=
            Declaración_de_variable | Declaración_de_función
        """
        nodos = []
        while (
            self.componente_actual is not None
            and self.componente_actual.texto in ["ingrediente", "receta"]
        ):
            if self.componente_actual.texto == "ingrediente":
                nodos.append(self.analizar_declaracion_variable())
            elif self.componente_actual.texto == "receta":
                nodos.append(self.analizar_funcion())
        return NodoArbol(TipoNodo.DECLARACION, nodos=nodos)

    def verificar_bloque_instrucciones(self):
        """
        Verifica que haya un bloque de instrucciones.
        Si no es así, lanza una excepción indicando el error.
        """
        instrucciones = []
        self.verificar_token(":")
        instrucciones.append(self.analizar_instruccion())

        while (
            self.componente_actual is not None
            and self.componente_actual.texto == ","
        ):
            self.verificar_token(",")
            instrucciones.append(self.analizar_instruccion())
        self.verificar_token(".")
        return NodoArbol(TipoNodo.BLOQUE_INSTRUCCIONES, nodos=instrucciones)

    def verificar_token(self, token_esperado):
        """
        Verifica que el componente léxico actual exista
        y coincida con el token esperado.
        Si no coincide, lanza una excepción indicando el error.
        Si no hay error, consume un token.

        Parámetros
        ----------
        token_esperado : str
            El token que se esperaba encontrar.
        """
        if self.componente_actual is None:
            raise Exception(
                f"Error de sintaxis: Fin de archivo inesperado: "
                f"se esperaba '{token_esperado}', "
                f"pero se llegó al final del archivo\n"
                f"--> línea {self.componentes_lexicos[-1].linea}, "
                f"columna {self.componentes_lexicos[-1].columna}"
            )
        elif self.componente_actual.texto != token_esperado:
            raise Exception(
                f"Error de sintaxis: Token inesperado: "
                f"Se esperaba '{token_esperado}', "
                f"pero se encontró '{self.componente_actual.texto}'\n"
                f"--> línea {self.componente_actual.linea}, "
                f"columna {self.componente_actual.columna}"
            )
        self.__siguiente()

    def analizar_parametros_inovocacion(self):
        """
        Analiza los parámetros en una invocación de función.

        Parámetros_de_invocación ::=
            Valor {',' Valor }
        """
        parametros = []
        parametros.append(self.analizar_valor())
        while (
            self.componente_actual is not None
            and self.componente_actual.texto == ";"
        ):
            self.verificar_token(";")
            parametros.append(self.analizar_valor())
        return NodoArbol(TipoNodo.PARAMETROS, nodos=parametros)

    def analizar_invocacion(self):
        """
        Invocación ::= Identificador "(" Parámetros_de_invocación? ")"
        """
        nodos = []
        nodos.append(self.verificar_identificador())

        self.verificar_token("(")

        if self.componente_actual.texto != ")":
            nodos.append(self.analizar_parametros_inovocacion())

        self.verificar_token(")")

        return NodoArbol(TipoNodo.INVOCACION, nodos=nodos)

    def analizar_instruccion_identificador(self):
        nodos = []
        nodos.append(self.verificar_identificador())
        # asignacion
        if self.componente_actual.texto == "<-":
            self.verificar_token("<-")
            if self.componente_actual.tipo in (
                TipoComponente.ENTERO,
                TipoComponente.FLOTANTE,
                TipoComponente.STRING,
                TipoComponente.BOOLEANO,
                TipoComponente.CARACTER,
            ):
                nodos.append(self.analizar_literal())
            else:
                nodos.append(self.analizar_expresion())
            return NodoArbol(TipoNodo.ASIGNACION, nodos=nodos)
        # invocaion de funcion
        elif self.componente_actual.texto == "(":
            self.verificar_token("(")
            if self.componente_actual.texto != ")":
                nodos.append(self.analizar_parametros_inovocacion())
            self.verificar_token(")")
            return NodoArbol(TipoNodo.INVOCACION, nodos=nodos)
        # indexacion
        elif self.componente_actual.texto == "!!":
            self.verificar_token("!!")
            nodos.append(self.analizar_valor())
            return NodoArbol(TipoNodo.INDEXACION, nodos=nodos)
