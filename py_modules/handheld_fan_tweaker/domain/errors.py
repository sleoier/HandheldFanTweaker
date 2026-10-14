class FanCurvesError(Exception):
    pass


class InvalidCurve(FanCurvesError):
    pass


class NotEditable(FanCurvesError):
    pass


class UnknownProfile(FanCurvesError):
    pass


class NoFactoryCurve(FanCurvesError):
    pass
