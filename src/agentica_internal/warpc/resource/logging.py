from ...core.log import LogFlag
from ...core.print import MEDIUM

__all__ = [
    'LOG_VIRT',
    'LOG_VSTACK',
    'LOG_ENCR',
    'LOG_DECR',
    'ICON_I',
    'ICON_M',
    'ICON_O',
    'ICON_E',
    'ICON_A',
    'ICON_C0',
    'ICON_CM',
    'ICON_C1',
]

################################################################################

LOG_VIRT = LogFlag('VIRT')
LOG_VSTACK = LogFlag('__+VSTACK')
LOG_ENCR = LogFlag('ENCR')
LOG_DECR = LogFlag('DECR')

################################################################################

color = MEDIUM.R
ICON_I = color @ '-->'  # icon for incoming virtual resource request received
ICON_M = color @ '---'  # icon for incoming virtual resource request processing
ICON_O = color @ '<--'  # icon for incoming virtual resource request response
ICON_E = color @ '!!!'  # icon for incoming virtual resource request error

color = MEDIUM.O
ICON_A = color @ '...'  # icon for async

color = MEDIUM.P
ICON_C0 = color @ '@@@'  # icon for resource creation/description start
ICON_CM = color @ "---"  # icon for resource enumeration
ICON_C1 = color @ '^^^'  # icon for resource creation/description end
