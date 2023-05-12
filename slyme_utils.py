import logging 

def repeat_success(func):
    valid = False 
    while not valid:
        try:
            func()
            valid = True 
        except Exception: 
            pass

def char_limiter(input, max_chars=64):    
    if len(input) > max_chars:
        return input[:max_chars] + '...'
    else: 
        return input
    
def log_setup(logger_file, 
              log_level='DEBUG', 
              console_level='INFO', 
              format='%(name)s - %(levelname)s - %(message)s'):
    
    logging.basicConfig(filename=logger_file, filemode='w', format=format)
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))

    # Disable logging for the selenium module
    selenium_logger = logging.getLogger('selenium')
    selenium_logger.setLevel(logging.WARNING)

    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.WARNING)

    if console_level != None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, console_level))
        logger.addHandler(console_handler)

    return logger 
    