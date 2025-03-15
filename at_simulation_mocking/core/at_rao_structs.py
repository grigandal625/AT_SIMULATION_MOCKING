from dataclasses import dataclass
from typing import Union, List, TypedDict, Dict
from xml.etree.ElementTree import Element


@dataclass
class ResourceParameter:
    name: str
    value: Union[str, int, float, bool, None]


@dataclass
class Resource:
    name: str
    parameters: List[ResourceParameter]


class ResourceParameterDict(TypedDict):
    name: str
    value: Union[str, int, float, bool, None]


class ResourceDict(TypedDict):
    resource_name: str
    parameters: List[ResourceParameterDict]


class ResourceMPDict(TypedDict):
    resource_name: str


class TactDict(TypedDict):
    resources: List[ResourceMPDict]

def resource_to_mapped(resource: Resource) -> ResourceMPDict:
    return {
        'resource_name': resource.name,
        **{parameter.name: parameter.value for parameter in resource.parameters}
        
    }

def resource_from_mapped(data: ResourceMPDict) -> Resource:
    name=data.pop('resource_name')
    return Resource(
        name=name,
        parameters=[ResourceParameter(name=p_n, value=p_v) for p_n, p_v in data.items()]
    )

class SMRun:
    tacts: Dict[int, List[Resource]]

    def __init__(self, tacts: Dict[int, List[Resource]]):
        self.tacts = tacts

    @property
    def __dict__(self) -> List[TactDict]:
        return [
            {
                'resources': [
                    resource_to_mapped(resource) for resource in tact_resources
                ]
            } 
            for tact_resources in self.tacts.values()
        ]
               

    @staticmethod
    def from_tacts_dict(data: List[TactDict]) -> 'SMRun':
        return SMRun(
            tacts={
                i: [resource_from_mapped(r) for r in tact.get('resources')]
                for i, tact in enumerate(data)
            }
        )

    @staticmethod
    def from_at4_xml(element: Element) -> 'SMRun':
        def get_max_tact(e: Element):
            tact = 0
            for r in e:
                if int(r.attrib["Номер_такта"]) > tact:
                    tact = int(r.attrib["Номер_такта"])
            return tact
            
        def get_all_resources_for_tact(e: Element, tact: int):
            return [r for r in e if int(r.attrib["Номер_такта"]) == tact]
        
        max_tact = get_max_tact(element)

        tacts = {}

        for tact in range(1, max_tact + 1):
            tact_resources = []
            resources = get_all_resources_for_tact(element, tact)
            for resource_el in resources:
                r_name = resource_el.attrib["Имя_ресурса"]
                parameters = []
                for param in resource_el:
                    p_name = param.attrib["Имя_параметра"]
                    v = param.text
                    try:
                        v = float(v.replace(",", "."))
                        if int(v) == v:
                            v = int(v)
                    except:
                        pass

                    parameters.append(ResourceParameter(name=p_name, value=v))
                resource = Resource(name=r_name, parameters=parameters)
                tact_resources.append(resource)
            tacts[tact - 1] = tact_resources
        return SMRun(tacts)
    
    @property
    def max_tact(self) -> int:
        return max(*list(self.tacts.keys()))
