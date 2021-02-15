import pytest
from api.routes import hello_world


def test_hello_world():
    assert hello_world() == "hello world"