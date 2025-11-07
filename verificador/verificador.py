from utils.arbol import TipoNodo, NodoArbol


class VerificadorSemantico:
    """
    Verificador semántico para el lenguaje MacCódigo.
    Recorre el ASA, valida tipos, maneja alcances y decora el árbol con tipos.
    """

    def __init__(self, arbol_sintaxis, verbose=False):
        self.asa = arbol_sintaxis
        self.errores = []
        self.verbose = verbose

        # Pila de ámbitos: lista de diccionarios (nombre -> tipo)
        self.pila_ambitos = [{}]
        # Registro de funciones: nombre -> (tipo_retorno, [(tipo, nombre_param)])
        self.funciones = {}

        # Tipos permitidos en MacCódigo
        self.TIPOS_PRIMITIVOS = ["torta", "lechuga", "pepinillo", "tomate", "salsa"]
        self.TIPOS_COMPUESTOS = ["hamburguesa", "cajita", "cajita_lechuga"]

        # Reglas de compatibilidad y coerción
        self.COMPATIBLES = {
            ("torta", "lechuga"): "lechuga",
            ("lechuga", "torta"): "lechuga",
            ("tomate", "salsa"): "tomate",
            ("salsa", "tomate"): "tomate",
        }

    # ==========================================================
    # MÉTODO PRINCIPAL
    # ==========================================================
    def verificar(self):
        if not self.asa or not self.asa.raiz:
            self.errores.append("Error: el árbol de sintaxis abstracta está vacío.")
            return self.errores

        if self.verbose:
            print("=== INICIO DE VERIFICACIÓN SEMÁNTICA ===")

        self._verificar_programa(self.asa.raiz)

        if self.verbose:
            print("\n=== TABLAS DE SÍMBOLOS ===")
            self._imprimir_tablas()

            print("\n=== ÁRBOL DECORADO ===")
            self._imprimir_arbol(self.asa.raiz)

        return self.errores

    # ==========================================================
    # PROGRAMA
    # ==========================================================
    def _verificar_programa(self, nodo_programa):
        for nodo in nodo_programa.nodos:
            self._verificar_nodo(nodo)

    # ==========================================================
    # DESPACHADOR RECURSIVO
    # ==========================================================
    def _verificar_nodo(self, nodo):
        if nodo is None:
            return None

        if self.verbose:
            print(f"→ Verificando nodo {nodo.tipo.name} ({nodo.contenido or ''})")

        if nodo.tipo == TipoNodo.DECLARACION_VARIABLE:
            self._verificar_declaracion_variable(nodo)

        elif nodo.tipo == TipoNodo.ASIGNACION:
            self._verificar_asignacion(nodo)

        elif nodo.tipo == TipoNodo.DECLARACION_FUNCION:
            self._verificar_funcion(nodo)

        elif nodo.tipo == TipoNodo.RETORNO:
            self._verificar_retorno(nodo)

        elif nodo.tipo == TipoNodo.CONDICIONAL:
            self._verificar_condicional(nodo)

        elif nodo.tipo == TipoNodo.REPETICION:
            self._verificar_repeticion(nodo)

        elif nodo.tipo in [TipoNodo.BLOQUE_INSTRUCCIONES, TipoNodo.SECCION_CODIGO]:
            self._nuevo_ambito()
            for hijo in nodo.nodos:
                self._verificar_nodo(hijo)
            self._cerrar_ambito()

        elif nodo.tipo == TipoNodo.INVOCACION:
            self._verificar_invocacion(nodo)

        elif nodo.tipo == TipoNodo.EXPRESION:
            tipo = self._verificar_expresion(nodo)
            nodo.decorador = tipo  # ← Árbol decorado
            return tipo

        # Recorre hijos recursivamente
        for hijo in nodo.nodos or []:
            self._verificar_nodo(hijo)

    # ==========================================================
    # REGLAS SEMÁNTICAS
    # ==========================================================
    def _verificar_declaracion_variable(self, nodo):
        tipo = nodo.nodos[0].contenido
        nombre = nodo.nodos[1].contenido

        if nombre in self.pila_ambitos[-1]:
            self._error(f"Variable '{nombre}' redeclarada en el mismo ámbito.")
        else:
            self.pila_ambitos[-1][nombre] = tipo
            nodo.decorador = tipo

    def _verificar_asignacion(self, nodo):
        nombre = nodo.nodos[0].contenido
        tipo_var = self._buscar_variable(nombre)

        if not tipo_var:
            self._error(f"Variable '{nombre}' no declarada antes de su uso.")
            return

        tipo_exp = self._verificar_expresion(nodo.nodos[1])
        if tipo_exp and not self._compatibles(tipo_var, tipo_exp):
            self._error(f"Tipos incompatibles en asignación: '{tipo_var}' <- '{tipo_exp}'.")

        nodo.decorador = tipo_var

    def _verificar_funcion(self, nodo):
        nombre = nodo.nodos[0].contenido
        if nombre in self.funciones:
            self._error(f"Función '{nombre}' redeclarada.")
            return

        parametros = nodo.nodos[1]
        tipos_params = self._extraer_parametros(parametros)
        tipo_retorno = "void"
        self.funciones[nombre] = (tipo_retorno, tipos_params)
        nodo.decorador = f"func({', '.join(t for t, _ in tipos_params)}) -> {tipo_retorno}"

        self._nuevo_ambito()
        for tipo, ident in tipos_params:
            self.pila_ambitos[-1][ident] = tipo

        # Verificar bloque interno
        if len(nodo.nodos) > 2:
            self._verificar_nodo(nodo.nodos[-1])

        self._cerrar_ambito()

    def _verificar_retorno(self, nodo):
        if not nodo.nodos:
            self._error("Retorno sin valor.")
            return
        tipo_valor = self._verificar_expresion(nodo.nodos[0])
        nodo.decorador = tipo_valor

    def _verificar_condicional(self, nodo):
        cond = nodo.nodos[0]

        # Si es un nodo de tipo CONDICION (con comparador)
        if cond.tipo.name == "CONDICION":
            tipo_cond = self._verificar_expresion(cond)
            nodo.decorador = "salsa"
            return

        # Si es una expresión normal
        tipo_cond = self._verificar_expresion(cond)
        if tipo_cond != "salsa":
            self._error("La condición de '¿si?' debe ser de tipo 'salsa' (booleano).")

    def _verificar_repeticion(self, nodo):
        tipo_inicio = self._verificar_expresion(nodo.nodos[1])
        tipo_fin = self._verificar_expresion(nodo.nodos[2])
        if tipo_inicio != "torta" or tipo_fin != "torta":
            self._error("El rango del ciclo 'para' debe ser de tipo 'torta' (entero).")

    def _verificar_invocacion(self, nodo):
        nombre_func = nodo.nodos[0].contenido
        if nombre_func not in self.funciones:
            self._error(f"Función '{nombre_func}' no declarada antes de su invocación.")
            return

        tipo_ret, params_decl = self.funciones[nombre_func]
        params_llamada = self._contar_parametros_invocacion(nodo)

        if len(params_decl) != len(params_llamada):
            self._error(
                f"La función '{nombre_func}' espera {len(params_decl)} parámetros, "
                f"pero se pasaron {len(params_llamada)}."
            )

        nodo.decorador = tipo_ret

    # ==========================================================
    # EXPRESIONES
    # ==========================================================
    def _verificar_expresion(self, nodo):
        if nodo is None:
            return None

        # Literales
        if nodo.tipo == TipoNodo.ENTERO:
            return "torta"
        elif nodo.tipo == TipoNodo.FLOTANTE:
            return "lechuga"
        elif nodo.tipo == TipoNodo.STRING:
            return "tomate"
        elif nodo.tipo == TipoNodo.BOOLEANO:
            return "salsa"
        elif nodo.tipo == TipoNodo.IDENTIFICADOR:
            return self._buscar_variable(nodo.contenido)
        elif nodo.tipo == TipoNodo.COMPARADOR:
            return "salsa"

        # Condiciones del tipo (IDENTIFICADOR, COMPARADOR, ENTERO)
        if nodo.tipo.name == "CONDICION":
            # Verifica los lados y marca tipo booleano
            izq = self._verificar_expresion(nodo.nodos[0])
            der = self._verificar_expresion(nodo.nodos[-1])
            nodo.decorador = "salsa"
            return "salsa"

        # Expresiones compuestas normales
        if nodo.tipo == TipoNodo.EXPRESION and nodo.nodos:
            if any(hijo.tipo == TipoNodo.COMPARADOR for hijo in nodo.nodos):
                nodo.decorador = "salsa"
                return "salsa"

            tipo_izq = self._verificar_expresion(nodo.nodos[0])
            for i in range(1, len(nodo.nodos), 2):
                tipo_der = self._verificar_expresion(nodo.nodos[i + 1])
                if not self._compatibles(tipo_izq, tipo_der):
                    self._error(f"Operación inválida entre tipos '{tipo_izq}' y '{tipo_der}'.")
                tipo_izq = self._resolver_tipo(tipo_izq, tipo_der)
            nodo.decorador = tipo_izq
            return tipo_izq

        return None


    # ==========================================================
    # FUNCIONES AUXILIARES
    # ==========================================================
    def _buscar_variable(self, nombre):
        for ambito in reversed(self.pila_ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def _extraer_parametros(self, nodo):
        pares = []
        if not nodo or not nodo.nodos:
            return pares
        for i in range(len(nodo.nodos)):
            hijo = nodo.nodos[i]
            if hijo.tipo == TipoNodo.IDENTIFICADOR:
                tipo = nodo.nodos[i - 1].contenido if i > 0 else "desconocido"
                pares.append((tipo, hijo.contenido))
        return pares

    def _contar_parametros_invocacion(self, nodo):
        if len(nodo.nodos) < 2:
            return []
        params_node = nodo.nodos[1]
        if not params_node or not params_node.nodos:
            return []
        return [self._verificar_expresion(n) for n in params_node.nodos]

    def _compatibles(self, t1, t2):
        if not t1 or not t2:
            return True
        if t1 == t2:
            return True
        return (t1, t2) in self.COMPATIBLES

    def _resolver_tipo(self, t1, t2):
        if (t1, t2) in self.COMPATIBLES:
            return self.COMPATIBLES[(t1, t2)]
        if (t2, t1) in self.COMPATIBLES:
            return self.COMPATIBLES[(t2, t1)]
        return t1

    def _nuevo_ambito(self):
        self.pila_ambitos.append({})

    def _cerrar_ambito(self):
        self.pila_ambitos.pop()

    def _error(self, mensaje):
        self.errores.append(f"Error semántico: {mensaje}")

    # ==========================================================
    # IMPRESIÓN DE TABLAS Y ÁRBOL DECORADO
    # ==========================================================
    def _imprimir_tablas(self):
        for i, ambito in enumerate(self.pila_ambitos):
            print(f"\nÁmbito {i + 1}:")
            if not ambito:
                print("  (Vacío)")
            for nombre, tipo in ambito.items():
                print(f"  {nombre:<15} -> {tipo}")

        if self.funciones:
            print("\nFunciones declaradas:")
            for nombre, (tipo_ret, params) in self.funciones.items():
                params_txt = ", ".join(f"{t} {n}" for t, n in params)
                print(f"  {nombre}({params_txt}) -> {tipo_ret}")

    def _imprimir_arbol(self, nodo, nivel=0):
        if nodo is None:
            return
        indent = "  " * nivel
        decorador = f" [{nodo.decorador}]" if hasattr(nodo, "decorador") and nodo.decorador else ""
        print(f"{indent}- {nodo.tipo.name} {nodo.contenido or ''}{decorador}")
        for hijo in nodo.nodos or []:
            self._imprimir_arbol(hijo, nivel + 1)
