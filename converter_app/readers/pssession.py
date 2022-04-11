import logging
import json

from pathlib import Path

from .base import Reader

logger = logging.getLogger(__name__)


class PsSessionReader(Reader):
    identifier = 'pssession_reader'
    priority = 10

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if Path(self.file_name).suffix != '.pssession':
            result = False
        else:
            result = True

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []

        data = json.loads(self.file_content)
        for measurement in data['measurements']:
            # each measurement is a table
            table = {
                'metadata': {},
                'header': [],
                'columns': [],
                'rows': []
            }

            # add the methods field to the header
            table['header'] = measurement['method'].splitlines()

            # add measurement fields to the metadata
            table['metadata']['title'] = str(measurement['title'])
            table['metadata']['timestamp'] = str(measurement['timestamp'])
            table['metadata']['deviceused'] = str(measurement['deviceused'])
            table['metadata']['deviceserial'] = str(measurement['deviceserial'])
            table['metadata']['type'] = str(measurement['dataset']['type'])

            # exctract the columns
            columns = []
            for idx, values in enumerate(measurement['dataset']['values']):
                # each array is a column
                table['columns'].append({
                    'key': str(idx),
                    'name': 'Column #{} ({})'.format(idx, values['description'])
                })

                # append the "datavalues" to list data list of lists
                columns.append([datavalues['v'] for datavalues in values['datavalues']])

            # transpose data list of lists
            table['rows'] = list(map(list, zip(*columns)))

            tables.append(table)

        return tables

    def get_metadata(self):
        metadata = super().get_metadata()
        data = json.loads(self.file_content)
        metadata['type'] = data['type']
        return metadata
