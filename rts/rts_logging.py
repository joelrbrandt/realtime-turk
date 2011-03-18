import settings
import logging

def configure_logging():
    mylevel = logging.DEBUG
    try:
        newlevel = logging.__getattribute__(settings.RTS_LOG_LEVEL)
        if type(newlevel) == int:
            mylevel = newlevel
    except:
        pass # well, we can't log the error yet, can we!

    logging.basicConfig(level=mylevel,
                        format='[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s',
                        filename=settings.RTS_LOGFILE,
                        filemode='w')


# the first time (well, only time, since it's only imported once) call configure_logging

configure_logging()
