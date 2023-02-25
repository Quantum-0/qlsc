class Singleton(type):
    """Singleton metaclass"""
    _instances: dict = {}

    def __call__(cls, *args, **kwargs) -> 'Singleton':
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]