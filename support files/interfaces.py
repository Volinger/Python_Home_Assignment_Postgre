import sqlalchemy as sql
import sqlalchemy.orm


Base = sqlalchemy.orm.declarative_base()
TenGigabitEthernet = "TenGigabitEthernet"
Port_channel = "Port-channel"
GigabitEthernet = "GigabitEthernet"

def try_optional_parameter(dataframe, parameter): #for optional parameters, make entries null if not present
    try:
        result = dataframe[parameter]
    except KeyError:
        result = None
    return result

#defines table structure
class GenericInterfaceParser(Base):
    __tablename__ = "interfaces",
    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.VARCHAR)
    description = sql.Column(sql.VARCHAR)
    config = sql.Column(sql.JSON)
    port_channel_id = sql.Column(sql.Integer, sql.ForeignKey(id))
    max_frame_size = sql.Column(sql.Integer)

    #overwrite init to implement different parsing for other interfaces
    def __init__(self, interface_type, interface):
        self.name = interface_type + str(interface["name"])
        self.description = try_optional_parameter(interface, "description")
        self.max_frame_size = try_optional_parameter(interface, "mtu")
        self.config = [interface]
        self.port_channel_id = None


class PortChannelParser(GenericInterfaceParser):
    def __init__(self, interface_type, interface):
        super().__init__(interface_type, interface)


class GigabitEthernetParser(GenericInterfaceParser):
    def __init__(self, interface_type, interface):
        super().__init__(interface_type, interface)
        try:
            interfaces = GenericInterfaceParser
            port_channel = interface["Cisco-IOS-XE-ethernet:channel-group"]["number"]
            self.port_channel_id = sql.select([interfaces.id]).where(interfaces.name == f"Port-channel{port_channel}").scalar_subquery()
        except KeyError:
            self.port_channel_id = None


#selects interface class and initializes data from appropriate interface section
def select_parser(parser, interface):
    parsers = {
        TenGigabitEthernet: GigabitEthernetParser,
        Port_channel: PortChannelParser,
        GigabitEthernet: GigabitEthernetParser
    }
    return parsers[parser](parser, interface)

