===============================
SciPy Central Style Definitions
===============================

README
======

The style definitions are written on the top of Twitter Bootstrap v2.3.1. 
A copy of Twitter Bootstrap source code is in `bootstrap` folder.

The following files in `./deploy/media/css/` are generated from here
    * ``spc-bootstrap.css``
    * ``spc-extend.css``

* ``spc-boostrap.less`` contains custom boostrap settings
* ``spc-extend.less`` contains extended style definitions

Requirements
------------
* ``less>=1.4.1``

Configure
---------
Use the following command to generate css files

    ``$ lessc spc-extend.less ../css/spc-extend.css``

    ``$ lessc spc-bootstrap.less ../css/spc-bootstrap.css``

You can also use any less editor or tool for compiling. Please make sure you meet above requirements.
Previous versions of less compiler generate some duplicate css code.
