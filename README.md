jdleden
=======
[![Build Status](https://travis-ci.org/jonge-democraten/jdleden.svg?branch=master)](https://travis-ci.org/jonge-democraten/jdleden) [![Coverage Status](https://coveralls.io/repos/github/jonge-democraten/jdleden/badge.svg?branch=master)](https://coveralls.io/github/jonge-democraten/jdleden?branch=master) [![Dependency Status](https://gemnasium.com/jonge-democraten/jdleden.svg)](https://gemnasium.com/jonge-democraten/jdleden)  

This tool handles both department-spreadsheets and newsletter-subscriptions of the Jonge Democraten.

## Installation
```
$ git clone https://github.com/jonge-democraten/jdleden.git
$ virtualenv -p python3 env
$ source env/bin/activate
$ pip install -r requirements.txt
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
$ source env/bin/activate
$ python manage.py afdelingrondschuif membesr_list.xlsx
```

See https://trac.jongedemocraten.nl/wiki/UpdateLedenlijst
