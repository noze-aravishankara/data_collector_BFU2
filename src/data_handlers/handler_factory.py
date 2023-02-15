from data_handlers.file.csv.csv_handler import CSVHandler

class HandlerFactory:
    _handlers = {CSVHandler.name: CSVHandler}

    @classmethod
    def get_handlers_list(cls):
        return cls._handlers.keys()

    @classmethod
    def get_handlers_required_arguments(cls, handler_type):
        return cls._handlers[handler_type].get_required_arguments_to_build()

    @classmethod
    def create_handler(cls, handler_type, **kwargs):
        try:
            return cls._handlers[handler_type.lower()](**kwargs)
        except Exception as e:
            print("Couldn't create the handler due to {}".format(e))
            return None