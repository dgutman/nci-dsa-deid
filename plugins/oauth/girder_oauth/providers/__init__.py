import collections

from .google import Google
from .globus import Globus
from .github import GitHub
from .linkedin import LinkedIn
from .bitbucket import Bitbucket
from .microsoft import Microsoft
from .box import Box
from .cilogon import CILogon
from .una import Una


def addProvider(provider):
    idMap[provider.getProviderName()] = provider


idMap = collections.OrderedDict()


addProvider(Google)
addProvider(Globus)
addProvider(GitHub)
addProvider(LinkedIn)
addProvider(Bitbucket)
addProvider(Microsoft)
addProvider(Box)
addProvider(CILogon)
addProvider(Una)
