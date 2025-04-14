#Custom exeptions for RunControl/DCS of the QMTS

class DewPointError(Exception):
    # DewPoint is outside of required Limits
    pass


class TempError(Exception):
    # Temperature is outside of required Limits
    pass

class TimeOutError(Exception):
    # sub process ran to long, was killed
    pass

class HWTripError(Exception):
    # sub process ran to long, was killed
    pass

