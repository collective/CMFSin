import random
import DateTime
from zLOG import LOG, DEBUG, INFO

_policy = {}

_defaultDateTime = DateTime.DateTime('1 Jan 1900')

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

# function to return an item date and possibly a default value
def dateit(x):
    LOG('dateit',DEBUG, x)
    retval = _defaultDateTime 
    if x.has_key('date'):
        retval = DateTime.DateTime(x['date'])
    return retval

class RecentFirstDateOrderPolicy(OrderPolicy):
    name = 'recentfirst'
    def order(self, results, max_size=None):
        final = []
        try:
            for ch in results:
                info, d = ch
                final += d
            
            # sort the list by date
            decorated_list = [(dateit(x),x) for x in final]
            decorated_list.sort()
            final          = [y for (x,y) in decorated_list]
            final.reverse()

            if max_size:
                final=final[:max_size]
        except Exception, inst:
            LOG('Date Order Exception', INFO , inst )

        return final
class RecentLastDateOrderPolicy(OrderPolicy):
    name = 'recentlast'
    def order(self, results, max_size=None):
        final = []
        try:
            for ch in results:
                info, d = ch
                final += d
            
            # sort the list by date
            decorated_list = [(dateit(x),x) for x in final]
            decorated_list.sort()
            final          = [y for (x,y) in decorated_list]

            if max_size:
                final=final[:max_size]
        except Exception, inst:
            LOG('Date Order Exception', INFO , inst )

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
registerPolicy(RecentFirstDateOrderPolicy())
registerPolicy(RecentLastDateOrderPolicy())

