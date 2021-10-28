import sqlalchemy as sql
from sqlalchemy_utils import database_exists, create_database
import sqlalchemy.orm
import json
import interfaces


config_file = "support files/configClear_v2.json"
desired_interfaces = [interfaces.TenGigabitEthernet, interfaces.GigabitEthernet]
# db_data
user_name = "****"
password = "****"
address = "****"
db_name = "test_db"

engine = sql.create_engine(f"postgresql://{user_name}:{password}@{address}/{db_name}")
if not database_exists(engine.url):
    create_database(engine.url)

Session = sqlalchemy.orm.sessionmaker(engine)


def load_source_json():
    with open(config_file) as file:
        config_data = json.load(file)
    return config_data


def get_interface_section(config_data):
    interface_section = config_data["frinx-uniconfig-topology:configuration"]["Cisco-IOS-XE-native:native"]["interface"]
    return interface_section


def process_interface_section(interface_section, interfaces_to_process):
    for interface_type in interfaces_to_process:
        interface_list = interface_section[interface_type]
        for interface_instance in interface_list:
            current_parser = interfaces.select_parser(interface_type, interface_instance)
            session.add(current_parser)


def process_data():
    config_data = load_source_json()
    interface_section = get_interface_section(config_data)
    # Process Port Channels first separately, so that we can get their IDs from DB
    process_interface_section(interface_section, [interfaces.Port_channel])
    process_interface_section(interface_section, desired_interfaces)


# Perform parsing of JSON to PostgreSQL database
# Note: This does not handle situation when table already contains data which are being added to database - in such case
# it may be necessary to provide additional handling (either insert only new records, clean table, overwrite old data...
with Session() as session:
    interfaces.Base.metadata.create_all(bind=engine)
    process_data()
    session.commit()
