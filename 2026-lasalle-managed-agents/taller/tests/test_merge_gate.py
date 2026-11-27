"""Pruebas sin red de la regla de merge."""
from taller.merge_gate import evaluar_checks, evaluar_pr, salto_rompe, saltos_que_rompen


def pr(rama="vuln-patcher/jinja2", estado="open", fork=False):
    base = {"full_name": "ana/cafe"}
    return {"state": estado, "draft": False, "head": {"ref": rama, "repo": {"full_name": "otra/cafe" if fork else "ana/cafe"}},
            "base": {"repo": base}}


def archivo(nombre="requirements.txt", parche="@@ -1 +1 @@\n-jinja2==3.1.3\n+jinja2==3.1.6", mas=1, menos=1):
    return {"filename": nombre, "additions": mas, "deletions": menos, "patch": parche}


def test_bump_de_parche_pasa():
    assert evaluar_pr(pr(), [archivo()]).permitido


def test_bump_minor_en_1x_pasa_y_major_no():
    assert not salto_rompe("2.31.0", "2.32.5")
    assert salto_rompe("2.31.0", "3.0.0")
    assert salto_rompe("0.14.1", "0.15.0")


def test_major_se_niega():
    v = evaluar_pr(pr(), [archivo(parche="@@ -1 +1 @@\n-flask==2.3.3\n+flask==3.1.3")])
    assert not v.permitido and "2.3.3 -> 3.1.3" in v.motivo


def test_codigo_se_niega():
    v = evaluar_pr(pr(), [archivo("cafe/db.py", parche="@@ -1 +1 @@\n-x\n+y")])
    assert not v.permitido and "cafe/db.py" in v.motivo


def test_workflows_se_niegan_aunque_se_llamen_como_dependencias():
    assert not evaluar_pr(pr(), [archivo(".github/requirements.txt")]).permitido


def test_rama_fork_y_tamano():
    assert not evaluar_pr(pr(rama="fix/jinja"), [archivo()]).permitido
    assert not evaluar_pr(pr(fork=True), [archivo()]).permitido
    assert not evaluar_pr(pr(), [archivo(mas=30, menos=11)]).permitido


def test_checks():
    assert not evaluar_checks([]).permitido
    assert not evaluar_checks([{"name": "tests", "status": "in_progress"}]).permitido
    assert not evaluar_checks([{"name": "tests", "status": "completed", "conclusion": "failure"}]).permitido
    assert evaluar_checks([{"name": "tests", "status": "completed", "conclusion": "success"}]).permitido


def test_saltos_en_varios_hunks():
    parche = "@@ -1,2 +1,2 @@\n-jinja2==3.1.3\n+jinja2==3.1.6\n@@ -5 +5 @@\n-requests==2.31.0\n+requests==3.0.0"
    assert saltos_que_rompen(parche) == ["2.31.0 -> 3.0.0"]
