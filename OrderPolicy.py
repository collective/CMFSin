import random

_policy = {}

def registerPolicy(p):
    _policy[p.name] = p

def listPolicies():
    return _policy.keys()

def lookupPolicy(name, default=None):
    return _policy.get(name, default)

class OrderPolicy:
    name = None
    def order(self, results, max_size=None):
        """return the results ordered according to a policy"""
        raise NotImplementedError


class SimplePolicy(OrderPolicy):
    name = "simple"
    def order(self, results, max_size=None):
        """Just return the results cap'ed at size"""
        final = []
        for ch in results:
            info, d = ch
            final += d
            
        if max_size:
            final=final[:max_size]
        return final

class RandomPolicy(OrderPolicy):
    name = 'random'
    def order(self, results, max_size=None):
        final = []
        
        for ch in results:
            info, d = ch
            final += d
            
        random.shuffle(final)
        if max_size:
            final=final[:max_size]

        return final


defaultPolicy = SimplePolicy()
registerPolicy(defaultPolicy)
registerPolicy(RandomPolicy())

