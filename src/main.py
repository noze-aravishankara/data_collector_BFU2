### THIS IS THE EDDY VERSION

import sys

print(sys.path)

import time
import os
from observer import create_observers, Observer
from utility import config_utils, file_utils, logger
from MFC.sensirion.sensirion_sfc500 import ProgramCompleted, MFCUnableToStart
 
appConfig = config_utils.AppConfig("CONFIG/config.json", file_type='json')
observers = create_observers(appConfig)

try:
    for i in range(appConfig.cycle_period):
        logger.get_logger().info("Updating publishers: second {}".format(i + 1))
        # map(Observer.update, observers)
        stability_check = True if (i + 1) % appConfig.stability_window == 0 else False
        monitor_bool = True
        for observer in observers:
            observer.update(i + 1, monitor_bool, stability_check)
            monitor_bool = False
        time.sleep(1)

    # map(Observer.terminate, observers)
    for each in observers:
        each.terminate()

    logger.get_logger().info("\n***************** Successfully Closed Application.*****************\n")

except ProgramCompleted:
    import os

    for each in observers:
        each.terminate()
    logger.get_logger().info("\n***************** Successfully Closed Application.*****************\n")
    os._exit(1)
except MFCUnableToStart:
    import os

    logger.get_logger().info("\n***************** Unable to start MFCs... Closing Application.*****************\n")
    for each in observers:
        each.terminate()
    os._exit(1)
except KeyboardInterrupt:
    import os
    import traceback

    # traceback.print_exc()
    for each in observers:
        each.terminate()
    os._exit(1)
except Exception:
    import os
    import traceback

    traceback.print_exc()
    for each in observers:
        each.terminate()
    os._exit(1)
