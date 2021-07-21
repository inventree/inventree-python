import click
import yaml

from inventree.api import InvenTreeAPI
from inventree.part import Part


def load_file(file_path: str):
    ''' Safe load YAML file '''

    try:
        with open(file_path, 'r') as file:
            try:
                data = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(exc)
                return None
    except FileNotFoundError:
        return None

    return data


class InvenTreeCLI:
    """ InvenTree CLI Class """

    operations = {
        'part': ['get', 'create', 'update', 'delete'],
    }

    def __init__(self, config_file):
        self.api = None

        print('Connecting... ', end='')

        # Extract configuration data from file
        config_data = load_file(config_file)

        if config_data:
            server = config_data.get('server', None)
            username = config_data.get('username', None)
            password = config_data.get('password', None)

            if server and username and password:
                try:
                    self.api = InvenTreeAPI(server, username=username, password=password)
                except ConnectionRefusedError:
                    print('Error: check server configuration!')
                    return
        else:
            print('Error loading configuration file!')
            return

        if self.api:
            print('Connected.')
        else:
            print('Error creating API!')

    def check_operation(self, table, operation):
        if not operation:
            return False

        operations = self.list_operations(table)
        if operation.upper() in operations:
            return True
        
        return False

    def list_operations(self, table):
        return [operation.upper() for operation in self.operations.get(table, [])]

    def part(self, _function, category=None, id=None, name=None, description=None, revision=None, type=None):
        if _function.lower() == 'get':
            part = None

            # Check with ID
            if id:
                part_by_id = Part(self.api, pk=id)
                try:
                    if part_by_id.pk:
                        part = part_by_id
                except AttributeError:
                    pass
            else:
                # Download all parts from database
                db_parts = Part.list(self.api)
                
                for db_part in db_parts:
                    if db_part.name == name:
                        part = db_part
                        break
            
            return part
                        
        return None


@click.command()
@click.option('--config', required=True, help='Configuration File')
@click.argument('table', required=False)
@click.option('--op', required=False)
@click.option('--list', required=False, is_flag=True)
@click.option('--id', required=False)
@click.option('--name', required=False)
def main(config, table, op, list, id, name):
    if config:
        inventree_api = InvenTreeCLI(config)

    if inventree_api.api:
        if table:
            if list:
                print(f'[TABLE] {table.upper()} : ', end='')
                print(inventree_api.list_operations(table))
                exit(0)

            if op:
                print(f'[TABLE/OP] {table.upper()}', end='')
                if list:
                    print(inventree_api.list_operations(table))

                if inventree_api.check_operation(table, op):
                    print(f' : {op.upper()}')
                    if table == 'part':
                        if not name and not id:
                            print('Error: Missing part name or ID!')
                        else:
                            part = inventree_api.part(_function=op, id=id, name=name)

                            if part:
                                print(f'{part.IPN} | {part.name} | {part.revision}')
                            else:
                                if id:
                                    print(f'Error: Part with ID={id} does not exist!')
                                else:
                                    print(f'Error: Part with name={name} does not exist!')
                else:
                    print(f' - Operation "{op}" not allowed!')
            else:
                print('Missing operation!')
        else:
            return


if __name__ == '__main__':
    main()
