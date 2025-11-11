"""Generador de código Python para programas escritos en MacCódigo.

El módulo toma el árbol de sintaxis abstracta producido por el analizador y
produce un script de Python equivalente.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence, Set

from utils.arbol import ArbolSintaxisAbstracta, NodoArbol, TipoNodo


@dataclass
class ResultadoExpresion:
    """Representa el resultado de traducir una expresión del ASA."""

    codigo: str
    valor: Any = None
    constante: bool = False


class _GestorMemoria:
    """Administra los identificadores visibles en cada ámbito."""

    def __init__(self) -> None:
        self._pila: List[Set[str]] = [set()]

    def nuevo_ambito(self) -> None:
        self._pila.append(set())

    def salir_ambito(self) -> None:
        if len(self._pila) > 1:
            self._pila.pop()

    def declarar(self, nombre: str) -> None:
        self._pila[-1].add(nombre)

    def esta_declarado(self, nombre: str) -> bool:
        return any(nombre in ambito for ambito in reversed(self._pila))


class GeneradorCodigoPython:
    """Genera código Python a partir de un árbol de sintaxis abstracta."""

    TYPE_HINTS = {
        "torta": "int",
        "lechuga": "float",
        "pepinillo": "str",
        "tomate": "str",
        "salsa": "bool",
        "hamburguesa": "dict",
        "cajita": "list",
        "cajita_lechuga": "list",
    }

    DEFAULT_VALUES = {
        "torta": "0",
        "lechuga": "0.0",
        "pepinillo": "''",
        "tomate": '""',
        "salsa": "False",
        "hamburguesa": "{}",
        "cajita": "[]",
        "cajita_lechuga": "[]",
    }

    OPERATOR_MAP = {
        "+": "+",
        "-": "-",
        "mul": "*",
        "div": "/",
        "mod": "%",
        "and": "and",
        "or": "or",
    }

    COMPARATOR_MAP = {
        "=": "==",
        "!=": "!=",
        "<": "<",
        ">": ">",
        "<=": "<=",
        ">=": ">=",
    }

    BOOLEAN_MAP = {
        "mayonesa": True,
        "ketchup": False,
    }

    def __init__(self, arbol: Optional[ArbolSintaxisAbstracta], optimizaciones: bool = True) -> None:
        self.arbol = arbol
        self.optimizar = optimizaciones
        self.memoria = _GestorMemoria()
        self.globales: Set[str] = set()
        self._lineas_globales: List[str] = []
        self._lineas_funciones: List[str] = []
        self._lineas_principales: List[str] = []

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def generar(self) -> str:
        """Regresa el código Python equivalente al programa de entrada."""
        if not self.arbol or not self.arbol.raiz:
            return "# Programa vacío generado desde MacCódigo"

        self._lineas_globales.clear()
        self._lineas_funciones.clear()
        self._lineas_principales.clear()
        self.memoria = _GestorMemoria()
        self.globales.clear()

        self._procesar_programa(self.arbol.raiz)

        lineas: List[str] = [
            '"""Código generado automáticamente desde MacCódigo."""',
            "",
        ]

        if self._lineas_globales:
            lineas.extend(self._lineas_globales)
            lineas.append("")

        if self._lineas_funciones:
            lineas.extend(self._lineas_funciones)
            if lineas[-1] != "":
                lineas.append("")

        lineas.append("def main() -> None:")
        if not self._lineas_principales:
            lineas.append("    pass")
        else:
            lineas.extend(self._lineas_principales)
        lineas.append("")
        lineas.append('if __name__ == "__main__":')
        lineas.append("    main()")
        return "\n".join(lineas)

    # ------------------------------------------------------------------
    # Procesamiento de nodos principales
    # ------------------------------------------------------------------
    def _procesar_programa(self, nodo: NodoArbol) -> None:
        for hijo in nodo.nodos:
            if hijo is None:
                continue
            if hijo.tipo == TipoNodo.SECCION_DECLARACIONES:
                self._procesar_declaraciones(hijo)
            elif hijo.tipo == TipoNodo.SECCION_CODIGO:
                self._procesar_codigo_principal(hijo)

    def _procesar_declaraciones(self, nodo: NodoArbol) -> None:
        for hijo in nodo.nodos:
            if hijo is None:
                continue
            if hijo.tipo == TipoNodo.BLOQUE_DECLARACION_VARIABLE:
                for declaracion in hijo.nodos:
                    self._lineas_globales.extend(
                        self._render_declaracion_variable(declaracion, indent=0, scope="global")
                    )
            elif hijo.tipo == TipoNodo.DECLARACION_FUNCION:
                self._lineas_funciones.extend(self._render_funcion(hijo))

    def _procesar_codigo_principal(self, nodo: NodoArbol) -> None:
        bloque = nodo.nodos[0] if nodo.nodos else None
        cuerpo = self._generar_bloque(bloque, indent=1, scope="main", introducir_global=True)
        self._lineas_principales.extend(cuerpo)

    # ------------------------------------------------------------------
    # Renderizado de construcciones
    # ------------------------------------------------------------------
    def _render_declaracion_variable(self, nodo: NodoArbol, *, indent: int, scope: str) -> List[str]:
        tipo = nodo.nodos[0].contenido if nodo.nodos else None
        nombre = nodo.nodos[1].contenido if len(nodo.nodos) > 1 else "anonimo"
        expresion = nodo.nodos[2] if len(nodo.nodos) > 2 else None

        resultado = self._generar_expresion(expresion) if expresion else None
        if resultado:
            expr_codigo = resultado.codigo
        else:
            expr_codigo = self.DEFAULT_VALUES.get(tipo or "", "None")

        anotacion = self.TYPE_HINTS.get(tipo or "", "object")
        linea = f"{self._indent(indent)}{nombre}: {anotacion} = {expr_codigo}"

        self.memoria.declarar(nombre)
        if scope == "global":
            self.globales.add(nombre)
        return [linea]

    def _render_funcion(self, nodo: NodoArbol) -> List[str]:
        nombre = nodo.nodos[0].contenido if nodo.nodos else "funcion"
        parametros = nodo.nodos[1] if len(nodo.nodos) > 1 else None
        bloque = nodo.nodos[-1] if nodo.nodos else None

        firmas = self._render_parametros_declaracion(parametros)
        cabecera = f"def {nombre}({', '.join(firmas)}):"
        lineas = [cabecera]

        self.memoria.nuevo_ambito()
        for parametro in self._extraer_nombres_parametros(firmas):
            self.memoria.declarar(parametro)

        cuerpo = self._generar_bloque(bloque, indent=1, scope="func", introducir_global=True)
        if not cuerpo:
            cuerpo = [self._indent(1) + "pass"]
        lineas.extend(cuerpo)
        self.memoria.salir_ambito()
        if lineas[-1] != "":
            lineas.append("")
        return lineas

    def _generar_bloque(
        self,
        nodo: Optional[NodoArbol],
        *,
        indent: int,
        scope: str,
        introducir_global: bool = False,
    ) -> List[str]:
        if nodo is None:
            return []

        globales = []
        if introducir_global:
            globales = sorted(self._buscar_asignaciones_globales(nodo))

        lineas: List[str] = []
        self.memoria.nuevo_ambito()
        if globales:
            declaracion = f"{self._indent(indent)}global {', '.join(globales)}"
            lineas.append(declaracion)

        for hijo in nodo.nodos:
            if hijo is None:
                continue
            instrucciones, finaliza = self._generar_instruccion(hijo, indent=indent, scope=scope)
            lineas.extend(instrucciones)
            if finaliza:
                break

        self.memoria.salir_ambito()
        return lineas

    def _generar_instruccion(
        self, nodo: NodoArbol, *, indent: int, scope: str
    ) -> tuple[List[str], bool]:
        if nodo.tipo == TipoNodo.DECLARACION_VARIABLE:
            return (
                self._render_declaracion_variable(nodo, indent=indent, scope=scope),
                False,
            )
        if nodo.tipo == TipoNodo.ASIGNACION:
            destino = nodo.nodos[0].contenido
            expresion = nodo.nodos[1] if len(nodo.nodos) > 1 else None
            resultado = self._generar_expresion(expresion) if expresion else ResultadoExpresion("None")
            linea = f"{self._indent(indent)}{destino} = {resultado.codigo}"
            return [linea], False
        if nodo.tipo == TipoNodo.CONDICIONAL:
            return self._render_condicional(nodo, indent=indent, scope=scope), False
        if nodo.tipo == TipoNodo.REPETICION:
            return self._render_repeticion(nodo, indent=indent, scope=scope), False
        if nodo.tipo == TipoNodo.RETORNO:
            expresion = nodo.nodos[0] if nodo.nodos else None
            resultado = self._generar_expresion(expresion) if expresion else ResultadoExpresion("None")
            linea = f"{self._indent(indent)}return {resultado.codigo}"
            return [linea], True
        if nodo.tipo == TipoNodo.SIS:
            return self._render_sis(nodo, indent=indent), False
        if nodo.tipo == TipoNodo.INVOCACION:
            resultado = self._generar_expresion(nodo)
            return [f"{self._indent(indent)}{resultado.codigo}"], False
        if nodo.tipo == TipoNodo.EXPRESION:
            resultado = self._generar_expresion(nodo)
            return [f"{self._indent(indent)}{resultado.codigo}"], False
        return [], False

    def _render_condicional(self, nodo: NodoArbol, *, indent: int, scope: str) -> List[str]:
        condicion = nodo.nodos[0] if nodo.nodos else None
        evaluada = self._generar_expresion(condicion)

        if self.optimizar and evaluada.constante:
            rama = 1 if evaluada.valor else 2
            if len(nodo.nodos) > rama:
                bloque = nodo.nodos[rama]
                return self._generar_bloque(bloque, indent=indent, scope=scope)
            return []

        lineas = [f"{self._indent(indent)}if {evaluada.codigo}:"]
        cuerpo_si = nodo.nodos[1] if len(nodo.nodos) > 1 else None
        bloque_si = self._generar_bloque(cuerpo_si, indent=indent + 1, scope=scope)
        if not bloque_si:
            bloque_si = [self._indent(indent + 1) + "pass"]
        lineas.extend(bloque_si)

        if len(nodo.nodos) > 2:
            cuerpo_no = nodo.nodos[2]
            bloque_no = self._generar_bloque(cuerpo_no, indent=indent + 1, scope=scope)
            if not bloque_no:
                bloque_no = [self._indent(indent + 1) + "pass"]
            lineas.append(f"{self._indent(indent)}else:")
            lineas.extend(bloque_no)
        return lineas

    def _render_repeticion(self, nodo: NodoArbol, *, indent: int, scope: str) -> List[str]:
        if not nodo.nodos:
            return []

        variable = nodo.nodos[0].contenido
        inicio = nodo.nodos[1] if len(nodo.nodos) > 1 else None
        fin = nodo.nodos[2] if len(nodo.nodos) > 2 else None
        bloque = nodo.nodos[3] if len(nodo.nodos) > 3 else None

        expr_inicio = self._generar_expresion(inicio)
        expr_fin = self._generar_expresion(fin)

        if self.optimizar and expr_inicio.constante and expr_fin.constante and expr_inicio.valor > expr_fin.valor:
            comentario = (
                f"{self._indent(indent)}# Bucle omitido: rango vacío para {variable}"
            )
            return [comentario]

        self.memoria.declarar(variable)
        cabecera = (
            f"{self._indent(indent)}for {variable} in range({expr_inicio.codigo}, {expr_fin.codigo} + 1):"
        )
        cuerpo = self._generar_bloque(bloque, indent=indent + 1, scope=scope)
        if not cuerpo:
            cuerpo = [self._indent(indent + 1) + "pass"]
        return [cabecera, *cuerpo]

    def _render_sis(self, nodo: NodoArbol, *, indent: int) -> List[str]:
        parametros = nodo.nodos[0] if nodo.nodos else None
        argumentos = []
        if parametros:
            for hijo in parametros.nodos:
                resultado = self._generar_expresion(hijo)
                argumentos.append(resultado.codigo)
        llamada = f"print({', '.join(argumentos)})" if argumentos else "print()"
        return [f"{self._indent(indent)}{llamada}"]

    # ------------------------------------------------------------------
    # Expresiones
    # ------------------------------------------------------------------
    def _generar_expresion(self, nodo: Optional[NodoArbol]) -> ResultadoExpresion:
        if nodo is None:
            return ResultadoExpresion("None", None, True)

        if nodo.tipo == TipoNodo.ENTERO:
            valor = int(nodo.contenido)
            return ResultadoExpresion(str(valor), valor, True)
        if nodo.tipo == TipoNodo.FLOTANTE:
            valor = float(nodo.contenido)
            return ResultadoExpresion(repr(valor), valor, True)
        if nodo.tipo == TipoNodo.STRING:
            valor = ast.literal_eval(nodo.contenido)
            return ResultadoExpresion(repr(valor), valor, True)
        if nodo.tipo == TipoNodo.CARACTER:
            valor = ast.literal_eval(nodo.contenido)
            return ResultadoExpresion(repr(valor), valor, True)
        if nodo.tipo == TipoNodo.BOOLEANO:
            valor = self.BOOLEAN_MAP.get(nodo.contenido, nodo.contenido == "True")
            return ResultadoExpresion("True" if valor else "False", valor, True)
        if nodo.tipo == TipoNodo.IDENTIFICADOR:
            nombre = nodo.contenido
            if nombre in self.BOOLEAN_MAP:
                valor = self.BOOLEAN_MAP[nombre]
                return ResultadoExpresion("True" if valor else "False", valor, True)
            return ResultadoExpresion(nombre, None, False)
        if nodo.tipo == TipoNodo.INVOCACION:
            return ResultadoExpresion(self._render_invocacion(nodo), None, False)
        if nodo.tipo == TipoNodo.INDEXACION:
            return ResultadoExpresion(self._render_indexacion(nodo), None, False)
        if nodo.tipo == TipoNodo.COMPARADOR:
            simbolo = self.COMPARATOR_MAP.get(nodo.contenido, nodo.contenido)
            return ResultadoExpresion(simbolo, None, False)
        if nodo.tipo == TipoNodo.CONDICION:
            return self._generar_condicion(nodo)
        if nodo.tipo == TipoNodo.PARAMETROS:
            argumentos = [self._generar_expresion(h).codigo for h in nodo.nodos]
            return ResultadoExpresion(", ".join(argumentos), None, False)
        if nodo.tipo == TipoNodo.EXPRESION:
            return self._generar_expresion_compuesta(nodo)

        if nodo.contenido is not None and not nodo.nodos:
            return ResultadoExpresion(nodo.contenido, None, False)

        if nodo.nodos:
            return self._generar_expresion(nodo.nodos[0])

        return ResultadoExpresion("None", None, True)

    def _generar_condicion(self, nodo: NodoArbol) -> ResultadoExpresion:
        if len(nodo.nodos) < 3:
            return ResultadoExpresion("False", False, True)
        izquierda = self._generar_expresion(nodo.nodos[0])
        comparador = nodo.nodos[1]
        derecha = self._generar_expresion(nodo.nodos[2])
        simbolo = self.COMPARATOR_MAP.get(comparador.contenido, comparador.contenido)

        if self.optimizar and izquierda.constante and derecha.constante:
            valor = self._evaluar_comparacion(simbolo, izquierda.valor, derecha.valor)
            return ResultadoExpresion("True" if valor else "False", valor, True)

        codigo = f"({izquierda.codigo} {simbolo} {derecha.codigo})"
        return ResultadoExpresion(codigo, None, False)

    def _generar_expresion_compuesta(self, nodo: NodoArbol) -> ResultadoExpresion:
        if not nodo.nodos:
            if nodo.contenido is not None:
                return ResultadoExpresion(str(nodo.contenido), nodo.contenido, False)
            return ResultadoExpresion("None", None, True)

        if len(nodo.nodos) == 1:
            return self._generar_expresion(nodo.nodos[0])

        resultado = self._generar_expresion(nodo.nodos[0])
        codigo = resultado.codigo
        constante = resultado.constante
        valor = resultado.valor

        indice = 1
        while indice < len(nodo.nodos):
            operador = nodo.nodos[indice]
            if indice + 1 >= len(nodo.nodos):
                break
            derecho = nodo.nodos[indice + 1]
            resultado_der = self._generar_expresion(derecho)
            simbolo = self.OPERATOR_MAP.get(operador.contenido, operador.contenido)

            if (
                self.optimizar
                and constante
                and resultado_der.constante
            ):
                evaluado = self._evaluar_operacion(simbolo, valor, resultado_der.valor)
                if evaluado is not None:
                    valor = evaluado
                    codigo = self._literal_python(evaluado)
                    constante = True
                else:
                    izquierda = self._literal_python(valor) if constante else codigo
                    codigo = f"({izquierda} {simbolo} {resultado_der.codigo})"
                    constante = False
            else:
                izquierda = self._literal_python(valor) if constante else codigo
                codigo = f"({izquierda} {simbolo} {resultado_der.codigo})"
                constante = False
            indice += 2
        return ResultadoExpresion(codigo, valor if constante else None, constante)

    def _render_invocacion(self, nodo: NodoArbol) -> str:
        if not nodo.nodos:
            return "()"
        nombre = nodo.nodos[0].contenido
        argumentos = []
        if len(nodo.nodos) > 1:
            argumentos = [
                self._generar_expresion(param).codigo
                for param in nodo.nodos[1].nodos
            ]
        return f"{nombre}({', '.join(argumentos)})"

    def _render_indexacion(self, nodo: NodoArbol) -> str:
        if not nodo.nodos:
            return "[]"
        base = nodo.nodos[0].contenido
        indice = self._generar_expresion(nodo.nodos[1]).codigo if len(nodo.nodos) > 1 else "0"
        return f"{base}[{indice}]"

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _render_parametros_declaracion(self, nodo: Optional[NodoArbol]) -> List[str]:
        if nodo is None:
            return []
        parametros: List[str] = []
        tipo_actual: Optional[str] = None
        for hijo in nodo.nodos:
            if hijo.tipo == TipoNodo.TIPO_DATO:
                tipo_actual = hijo.contenido
            elif hijo.tipo == TipoNodo.IDENTIFICADOR:
                if tipo_actual and tipo_actual in self.TYPE_HINTS:
                    parametros.append(f"{hijo.contenido}: {self.TYPE_HINTS[tipo_actual]}")
                else:
                    parametros.append(hijo.contenido)
                tipo_actual = None
            elif hijo.contenido:
                parametros.append(hijo.contenido)
        return parametros

    def _extraer_nombres_parametros(self, firmas: Sequence[str]) -> Iterable[str]:
        for firma in firmas:
            nombre = firma.split(":", 1)[0].strip()
            if nombre:
                yield nombre

    def _indent(self, nivel: int) -> str:
        return "    " * nivel

    def _literal_python(self, valor: Any) -> str:
        if isinstance(valor, str):
            return repr(valor)
        if isinstance(valor, bool):
            return "True" if valor else "False"
        return repr(valor)

    def _evaluar_operacion(self, operador: str, izquierda: Any, derecha: Any) -> Optional[Any]:
        try:
            if operador == "+":
                return izquierda + derecha
            if operador == "-":
                return izquierda - derecha
            if operador == "*":
                return izquierda * derecha
            if operador == "/":
                return izquierda / derecha
            if operador == "%":
                return izquierda % derecha
            if operador == "and":
                return izquierda and derecha
            if operador == "or":
                return izquierda or derecha
        except Exception:
            return None
        return None

    def _evaluar_comparacion(self, operador: str, izquierda: Any, derecha: Any) -> bool:
        if operador == "==":
            return izquierda == derecha
        if operador == "!=":
            return izquierda != derecha
        if operador == "<":
            return izquierda < derecha
        if operador == ">":
            return izquierda > derecha
        if operador == "<=":
            return izquierda <= derecha
        if operador == ">=":
            return izquierda >= derecha
        return False

    def _buscar_asignaciones_globales(self, nodo: NodoArbol) -> Set[str]:
        encontrados: Set[str] = set()
        for hijo in nodo.nodos or []:
            if hijo is None:
                continue
            if hijo.tipo == TipoNodo.ASIGNACION:
                destino = hijo.nodos[0].contenido
                if destino in self.globales:
                    encontrados.add(destino)
            elif hijo.tipo == TipoNodo.CONDICIONAL:
                for rama in hijo.nodos[1:]:
                    encontrados |= self._buscar_asignaciones_globales(rama)
            elif hijo.tipo == TipoNodo.REPETICION:
                if len(hijo.nodos) > 3:
                    encontrados |= self._buscar_asignaciones_globales(hijo.nodos[3])
            elif hijo.tipo == TipoNodo.BLOQUE_INSTRUCCIONES:
                encontrados |= self._buscar_asignaciones_globales(hijo)
        return encontrados


__all__ = ["GeneradorCodigoPython", "ResultadoExpresion"]
