# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2016
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------
from pixiedust.display.display import *
from pixiedust.utils import Logger
from six import with_metaclass, iteritems
from abc import ABCMeta
import inspect

def route(**kw):
    def route_dec(fn):
        fn.pixiedust_route=kw
        return fn
    return route_dec

@Logger()
class PixieDustApp(with_metaclass(ABCMeta, Display)):

    routesByClass = {}
    
    def matchRoute(self, route):
        for key,value in iteritems(route):
            option = self.options.get(key,"false")
            if  option != value:
                return False
        return True
        
    def doRender(self, handlerId):
        if self.__class__.__name__ in PixieDustApp.routesByClass:
            defRoute = None
            for t in PixieDustApp.routesByClass[self.__class__.__name__]:
                if not t[0]:
                    defRoute = t[1]
                elif self.matchRoute(t[0]):
                    self.debug("match found: {}".format(t[0]))
                    getattr(self, t[1])()
                    return
            if defRoute:
                getattr(self, defRoute)()
                return

        print("Didn't find any routes for {}".format(self))
    
class PixieEntity(object):
    def __init__(self, entity=None):
        self.entity = entity

def PixieApp(cls):
    for name, method in iteritems(cls.__dict__):
        if hasattr(method, "pixiedust_route"):
            clsName = "{}_{}_Display".format(inspect.getmodule(cls).__name__, cls.__name__)
            if clsName not in PixieDustApp.routesByClass:
                PixieDustApp.routesByClass[clsName] = []
            PixieDustApp.routesByClass[clsName].append( (method.pixiedust_route,name) )

    def __init__(self, options, entity, dataHandler=None):
        PixieDustApp.__init__(self, options, entity, dataHandler)
        self.nostore_params = True

    def decoName(cls, suffix):
        return "{}_{}_{}".format(cls.__module__, cls.__name__, suffix)
        
    displayClass = type( decoName(cls, "Display"), (cls,PixieDustApp, ),{"__init__": __init__})
    entityClass = type("", (PixieEntity,), {})
    
    @addId
    def getMenuInfo(self, entity, dataHandler=None):
        if entity == entityClass or entity.__class__ == entityClass:
            return [{"id": decoName(cls, "id")}]
        return []
    
    displayHandlerMetaClass = type( decoName(cls, "Meta"), (DisplayHandlerMeta,), {
            "getMenuInfo": getMenuInfo,
            "newDisplayHandler": lambda self, options, entity: displayClass(options, entity)
        })
    
    displayHandlerMeta = displayHandlerMetaClass()
    registerDisplayHandler( displayHandlerMeta )
    return entityClass