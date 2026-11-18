"""Domain registry: feature extractors, generators, candidate actions per domain."""
from . import arith, percentile

REGISTRY = {'percentile': percentile.DOMAIN, 'arith': arith.DOMAIN}

try:  # added in step A2
    from . import procurement
    REGISTRY['procurement'] = procurement.DOMAIN
except ImportError:
    pass
