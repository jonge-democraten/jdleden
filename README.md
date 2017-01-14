jdleden
=======
[![Build Status](https://travis-ci.org/jonge-democraten/jdleden.svg?branch=master)](https://travis-ci.org/jonge-democraten/jdleden) [![Coverage Status](https://coveralls.io/repos/github/jonge-democraten/jdleden/badge.svg?branch=master)](https://coveralls.io/github/jonge-democraten/jdleden?branch=master) [![Dependency Status](https://gemnasium.com/jonge-democraten/jdleden.svg)](https://gemnasium.com/jonge-democraten/jdleden)  

This tool updates [hemres](https://github.com/jonge-democraten/hemres) newsletter-subscriptions and the LDAP, based on an excel file with member information.

Requires Python 3.4+

## Installation
```
$ git clone https://github.com/jonge-democraten/jdleden.git
$ virtualenv -p python3 env
$ source env/bin/activate
$ pip install -r requirements.txt
$ python create_local_settings.py
```

Copy `jdleden/local_settings_example.py`, name it `jdleden/local_settings.py` and set the settings inside.


## Configuration
All settings can be found in `local_settings.py`.


## Usage
Activate the virtual env before using any of the management commands below,
```
$ source env/bin/activate
```

Update members,
```
$ python manage.py updateleden old_list.xlsx new_list.xlsx
```

Update after change in departments,
```
$ python manage.py afdelingrondschuif members_list.xlsx
```

Create members per department excel output,
```
$ python manage.py createdepartmentexcels members_list.xlsx
```

See https://trac.jongedemocraten.nl/wiki/UpdateLedenlijst


## Development and Design

jdleden uses [hemres](https://github.com/jonge-democraten/hemres) to update newsletter subscriptions. 

jdleden uses python-ldap to update LDAP. 

Django and Mezzanine are required because hemres depends on them.


