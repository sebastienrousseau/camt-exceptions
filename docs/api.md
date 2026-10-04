# Python API reference

The importable Python surface: the generation engine the tools wrap, and
the server module whose handlers can be called in-process without a
transport.

```{eval-rst}
.. automodule:: camt_exceptions
   :members:
   :undoc-members:
```

## Generation engine

```{eval-rst}
.. automodule:: camt_exceptions.generator
   :members:
   :undoc-members:
   :show-inheritance:
```

## Tool, prompt and resource module

Every tool, the prompt and both resources are plain functions registered
on the ``server`` object at import time, so they can be called in-process
without a transport.

```{eval-rst}
.. automodule:: camt_exceptions.server
   :members:
   :undoc-members:
   :show-inheritance:
```

## Transports and command line

```{eval-rst}
.. automodule:: camt_exceptions._transports
   :members:

.. automodule:: camt_exceptions._cli
   :members:
```
