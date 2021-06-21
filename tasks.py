# -*- coding: utf-8 -*-

try:
    from invoke import ctask as task
except ImportError:
    from invoke import task


@task
def style(c):
    """
    Run PEP style checks against the codebase
    """

    print("Running PEP code style checks...")
    c.run('flake8 .')
