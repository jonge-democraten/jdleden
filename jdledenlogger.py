import os
import logging

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))

# Set up logging to console, debug.log and info.log
logger = logging.getLogger('jdleden')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
fhd = logging.FileHandler(os.path.join(SCRIPTDIR, "debug.log"))
fhd.setLevel(logging.DEBUG)
fhi = logging.FileHandler(os.path.join(SCRIPTDIR, "info.log"))
fhi.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
ch.setFormatter(formatter)
fhd.setFormatter(formatter)
fhi.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fhd)
logger.addHandler(fhi)