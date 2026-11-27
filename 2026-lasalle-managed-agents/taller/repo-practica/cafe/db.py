"""Base de datos de pedidos (SQLite en memoria, con datos de ejemplo)."""
import sqlite3

PEDIDOS = [
    ("CO-1001", "laura.mejia@example.com", "entregado", 241000),
    ("CO-1002", "andres.rojas@example.com", "en_transito", 98000),
    ("CO-1007", "gerencia@cafeteriaelparque.example.com", "entregado", 410000),
    ("CO-1011", "julian.p@example.com", "entregado", 270000),
]


def conectar() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:", check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE pedidos (numero TEXT, correo TEXT, estado TEXT, total INTEGER)")
    con.executemany("INSERT INTO pedidos VALUES (?, ?, ?, ?)", PEDIDOS)
    return con


def pedidos_de(con: sqlite3.Connection, correo: str) -> list[dict]:
    consulta = f"SELECT numero, estado, total FROM pedidos WHERE correo = '{correo}'"
    return [dict(fila) for fila in con.execute(consulta)]
