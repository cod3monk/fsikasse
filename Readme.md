# FSI-Kasse

## Description

...


## Installation


### Install Flask

Have a look at the installation instructions at the [Flask website](http://flask.pocoo.org/docs/0.10/installation/). The most important steps are listed here.

On MacOS X or GNU/Linux, run one of the following:

    $ sudo pip install virtualenv

or

    $ sudo easy_install virtualenv

On Ubuntu, you can use

    $ sudo apt-get install python-virtualenv

Get and activate the latest flask version:

    $ git clone http://github.com/mitsuhiko/flask.git
    Cloning into 'flask'...
    ...
    $ cd flask
    $ virtualenv venv --distribute
    New python executable in venv/bin/python
    Installing distribute............done.
    $ . venv/bin/activate
    $ python setup.py develop
    ...
    Finished processing dependencies for Flask

### Dependencies

Install [Pillow](https://pypi.python.org/pypi/Pillow/2.1.0)

    $ pip install Pillow

### Install FSI-Kasse

Download and extract fsikasse or clone the git repository.

To initialize the database, run in the fsikasse-directory

    $ flask --app=fsikasse initdb 

And start the app with

    $ flask --app=fsikasse run                

From now on, it is sufficient to run in the flask-directory

    $ . venv/bin/activate

and then start the app in the fsikasse-directory with

    $ flask --app=fsikasse run