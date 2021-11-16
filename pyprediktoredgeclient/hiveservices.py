__all__ = 'nstance_identifiers', 'list_instances', 'get_instance', 'remove_instance', 'add_instance', 'HiveInstance'

from .util import Prediktor, Error
import os
import clr
import uuid
from System import Action, Func

InstanceService = Prediktor.APIS.Hive.HiveInstanceService

def instance_identifiers():
	return [uuid.UUID(guid.ToString()) for guid in InstanceService.GetRegisteredInstances()]

def _create_instance_service():
    def isrunning(a):
        mutex_name = "" if not a.ProgId else f"Global\\{a.ProgId}"
        return Prediktor.APIS.Utilities.InstanceRunningMutex.IsRunning(mutex_name)

    pathfinder = Prediktor.APIS.Utilities.ComServerPathFinder()
    return Prediktor.APIS.Hive.HiveInstanceService(pathfinder, Func[Prediktor.APIS.Utilities.IApisInstance, bool] (isrunning))

def _get_instance(service, name):
    for inst in service.GetInstances():
        if inst.InstanceName == name:
            return inst
    raise Error('Instance not found')


def list_instances():
    """
    Return a list of all registered hive instances

    Returns: List[HiveInstance]
    """
    service = _create_instance_service()
    return [HiveInstance(inst) for inst in service.GetInstances()]

def get_instance(name):
    """
    Return the hive instance with the instance name `name`

    Arguments:
    name string: the Name of the instance.

    Returns: HiveInstance
    """
    return HiveInstance(_get_instance(_create_instance_service(), name))    

def remove_instance(inst):
    """
    Remove an instance.

    Arguments:
    inst: string or HiveInstance. the instance that should be removed
    """
    service = _create_instance_service()

    if isinstance(inst, str):
        inst = _get_instance(service, inst)
    elif isinstance(inst, HiveInstance):
        raise Error('Unsupported type for instance lookup')

    service.RemoveInstance(inst.CLSID)

def add_instance(name, as_service=True):
    """
    Add a new instance to the system

    Arguments:
    name: string. The name of the new service
    as_service: Optional bool. Switch that determines whether the instance is created as a service or COM-server
    """
    service = _create_instance_service()
    service.AddInstance(name, as_service)
    return get_instance(name)


class HiveInstance:
    """
    A class representing an installed Hive service. The service can be started or stopped from the running property. 
    """
    def __init__(self, api):
        self.api = api

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Apis.Hive instance-service: {self.prog_id}>"

    
    prog_id = property(lambda self:self.api.ProgId)
    is_default = property(lambda self:self.api.IsDefaultInstance)
    name = property(lambda self:self.api.InstanceName)
    CLSID = property(lambda self:uuid.UUID(self.api.CLSID.ToString()))

    def _running(self):
        return self.api.IsRunning

    def _set_running(self, wanted:bool):
        current = self.api.IsRunning
        if wanted and not current:
            os.popen(f"sc start {self.name}")
        elif not wanted and current:
            os.popen(f"sc stop {self.name}")

    running = property(_running, _set_running, doc="get or set the running state of the instance")

