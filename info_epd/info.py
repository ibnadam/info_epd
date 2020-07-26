from base import *
from mixins.salah import *
from config import *


class Info(Base, SalahMixin):
    """Compose our Info object

    Always inherit from Base
    Next add mixins that will contribute to Info

    Be sure to call base/mixin class constructors
    """
    def __init__(self):
        Base.__init__(self)
        SalahMixin.__init__(self)


def main():
    try:
        info = Info()
        info.run()
    except IOError as e:
        logging.error(e)
    except KeyboardInterrupt:    
        logging.info("Quitting")


if __name__ == '__main__':
    main()
    
