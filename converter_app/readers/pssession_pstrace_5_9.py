import json
import logging

from .base import Reader

logger = logging.getLogger(__name__)


class PsSessionReader(Reader):
    identifier = 'pssession_reader_pstrace_5_9'
    priority = 10

    def check(self):
        if self.file.suffix != '.pssession':
            result = False
        else:
            result = True

        logger.debug('result=%s', result)
        return result

    def parse_json(self):
        try:
            return json.loads(self.file.content.strip(b'\xfe\xff'))
        except json.decoder.JSONDecodeError:
            return {}

    def get_tables(self):
        tables = []
        data = self.parse_json()

        for measurement in data.get('Measurements', []):
            # each measurement is a table
            table = self.append_table(tables)

            # add the method field to the header
            table['header'] = measurement['Method'].splitlines()

            # add key value pairs from the method field to the metadata
            for line in table['header']:
                if not line.startswith('#'):
                    try:
                        key, value = line.strip().split('=')
                        table['metadata'][key] = value
                    except ValueError:
                        pass

            # add measurement fields to the metadata
            table['metadata']['title'] = str(measurement['Title'])
            table['metadata']['timestamp'] = str(measurement['TimeStamp'])
            table['metadata']['deviceused'] = str(measurement['DeviceUsed'])
            table['metadata']['deviceserial'] = str(measurement['DeviceSerial'])
            table['metadata']['type'] = str(measurement['DataSet']['Type'])

            # exctract the columns
            columns = []
            for idx, values in enumerate(measurement['DataSet']['Values']):
                # each array is a column
                column_name = values['description']

                # add the column name to the metadata
                table['metadata']['column_{:02d}'.format(idx)] = column_name

                # add the column name to list of columns
                table['columns'].append({
                    'key': str(idx),
                    'name': 'Column #{} ({})'.format(idx, column_name)
                })

                # append the "datavalues" to list data list of lists
                columns.append([datavalues['v'] for datavalues in values['DataValues']])

            # transpose data list of lists
            table['rows'] = list(map(list, zip(*columns)))

            # add number of rows and columns to metadata
            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))

        return tables

    def get_metadata(self):
        metadata = super().get_metadata()
        data = self.parse_json()
        metadata['type'] = data.get('type')
        return metadata
