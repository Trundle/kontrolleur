.. image:: https://img.shields.io/badge/fish--shell-2.3.0-blue.svg
   :target: https://github.com/fish-shell/fish-shell/releases/tag/2.3.0

.. image:: https://img.shields.io/github/license/Trundle/kontrolleur.svg
   :target: https://www.tldrlegal.com/l/mit

.. image:: https://travis-ci.org/Trundle/kontrolleur.svg?branch=master
   :target: https://travis-ci.org/Trundle/kontrolleur

===========
Kontrolleur
===========

Like Ctrl-r, but for the `fish shell <http://fishshell.com/>`_


Requirements
============

* Python 3.3 (or newer)
* fish 2.3.0 (or newer)


Installation
============

For installing the ``kontrolleur`` executable, you can use pip::

  pip install --user https://github.com/Trundle/kontrolleur/archive/master.zip

This will install kontrolleur to ``~/.local/bin/``.

For integration with the fish-shell, you can use `fisher
<https://github.com/jorgebucaran/fisher>`_::

  fisher add Trundle/kontrolleur

Note that this expects the ``kontrolleur`` executable in ``$PATH``.


License
=======

MIT/Expat. See ``LICENSE`` for details.
