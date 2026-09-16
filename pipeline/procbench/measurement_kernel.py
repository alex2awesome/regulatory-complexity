"""Optional native Student-t(4) interval kernel, checked against SciPy.

For t=|x|/sqrt(4+x^2), S_4(|x|)=(1-t)^2(2+t)/4. Compute
1-t=4/[hypot(x,2)*(hypot(x,2)+|x|)] to avoid positive-tail cancellation.
No fast-math or parallel reductions; this accelerates, not changes, the likelihood.
"""
import math
import numpy as np

try:
    from numba import njit
    import numba
except ImportError:
    njit=None
    numba=None


def student4_survival_abs(x):
    if math.isinf(x):
        return 0.
    h=math.hypot(x,2.)
    t=x/h
    complement=4./(h*(h+x))
    return .25*complement*complement*(2.+t)


def student4_interval(lower,upper,location,scale):
    lo=(lower-location)/scale
    hi=(upper-location)/scale
    if lo>0:
        probability=student4_survival_abs(lo)-student4_survival_abs(hi)
    else:
        lower_cdf=student4_survival_abs(abs(lo))
        upper_cdf=student4_survival_abs(abs(hi)) if hi<0 else 1.-student4_survival_abs(hi)
        probability=upper_cdf-lower_cdf
    return max(probability,1e-300)


if njit is not None:
    student4_survival_abs=njit(cache=True)(student4_survival_abs)
    student4_interval=njit(cache=True)(student4_interval)


def observation_loop(lower,upper,base,offset,shifts,weights,scale,contamination,progress,completion):
    result=np.empty(len(base))
    for i in range(len(base)):
        completed,ongoing=0.,0.
        for j in range(len(shifts)):
            loc=base[i]+offset+shifts[j]
            p=(1-contamination)*student4_interval(lower,upper,loc,scale)+contamination*student4_interval(lower,upper,loc,2.)
            completed+=weights[j]*p
            if completion<1.:
                loc+=math.log(max(progress,1e-15))
                p=(1-contamination)*student4_interval(lower,upper,loc,scale)+contamination*student4_interval(lower,upper,loc,2.)
                ongoing+=weights[j]*p
        result[i]=math.log(max(completion*completed+(1-completion)*ongoing,1e-300))
    return result


observation_native=njit(cache=True)(observation_loop) if njit is not None else None
ACCELERATOR=f'numba/{numba.__version__}' if numba is not None else 'scipy'
