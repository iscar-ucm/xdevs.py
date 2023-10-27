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
              'tcp_handler = xdevs.plugins.input_handlers.tcp_input_handler:TCPInputHandler',
              'mqtt_handler = xdevs.plugins.input_handlers.mqtt_input_handler:MQTTInputHandler',

          ],

          'xdevs.plugins.output_handlers': [
              'csv_out_handler = xdevs.plugins.output_handlers.csv_output_handler:CSVOutputHandler',
              'tcp_out_handler = xdevs.plugins.output_handlers.tcp_output_handler:TCPOutputHandler',
              'mqtt_handler = xdevs.plugins.output_handlers.mqtt_output_handler:MQTTOutputHandler',
          ],

          'xdevs': [
              'Generator = xdevs.examples.basic.basic:Generator',
              'Transducer = xdevs.examples.basic.basic:Transducer',
              'Processor = xdevs.examples.basic.basic:Processor',
              'GPT = xdevs.examples.basic.basic:Gpt',
              'EF = xdevs.examples.basic.efp_model:EF',
              'EFP = xdevs.examples.basic.efp_model:EFP'
          ],


          'xdevs.plugins.wrappers': [
              'pypdevs = xdevs.plugins.wrappers.pypdevs:PyPDEVSWrapper'
          ]},
      extras_require={
          'sql': ['sqlalchemy==1.3.22'],
          'elasticsearch': ['elasticsearch==7.10.1'],
      },
      zip_safe=False)
