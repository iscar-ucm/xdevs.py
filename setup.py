from setuptools import setup, find_packages

setup(name='xdevs',
      version='2.2.2',
      description='xDEVS M&S framework',
      url='https://github.com/iscar-ucm/xdevs.py',
      author='Román Cárdenas, Kevin Henares',
      author_email='r.cardenas@upm.es, khenares@ucm.es',
      packages=find_packages(exclude=['xdevs.tests']),
      entry_points={
          'xdevs.plugins.transducers': [
              'csv = xdevs.plugins.transducers.csv_transducer:CSVTransducer',
              'sql = xdevs.plugins.transducers.sql_transducer:SQLTransducer',
              'elasticsearch = xdevs.plugins.transducers.elasticsearch_transducer:ElasticsearchTransducer',
          ],

          'xdevs.plugins.input_handlers': [

              'function = xdevs.plugins.input_handlers.callable_function:CallableFunction',
              'csv_handler = xdevs.plugins.input_handlers.csv_input_handler:CSVInputHandler',

          ],

          'xdevs.plugins.wrappers': [
              'pypdevs = xdevs.plugins.wrappers.pypdevs:PyPDEVSWrapper'
          ]},
      extras_require={
          'sql': ['sqlalchemy==1.3.22'],
          'elasticsearch': ['elasticsearch==7.10.1'],
      },
      zip_safe=False)
