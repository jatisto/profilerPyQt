import datetime
import traceback


def handle_errors(log_file, text=''):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exp:
                error_msg = f"{text}\n{str(exp)}\n{traceback.format_exc()}"
                with open(f"Logs/{log_file}", 'a', encoding='utf-8') as log:
                    log.write(error_msg)
                write_log(f"Произошла ошибка: {str(exp)}", f"Logs/{log_file}")
                write_log(traceback.format_exc(), f"Logs/{log_file}")
            except KeyboardInterrupt as exp:
                error_msg: str = f"{text}\n{str(exp)}\n{traceback.format_exc()}"
                with open(f"Logs/{log_file}", 'a', encoding='utf-8') as log:
                    log.write(error_msg)
                write_log(f"Произошла ошибка: {str(exp)}", f"Logs/{log_file}")
                write_log(traceback.format_exc(), f"Logs/{log_file}")

        return wrapper

    return decorator


def write_log(text_log, log_file="base_log_file.log") -> None:
    with open(f"Logs/{log_file}", 'a', encoding='utf-8') as log:
        log.write('\n')
        log.write(f'{datetime.datetime.now()} - {text_log}\n')


def basis_handle_errors(text=''):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exp:
                error_msg = f"{text}\n{str(exp)}\n{traceback.format_exc()}"
                with open('base_error_log.log', 'a', encoding='utf-8') as log:
                    log.write(error_msg)
                write_log(f"Произошла ошибка: {str(exp)}", 'base_error_log.log')
                write_log(traceback.format_exc(), 'base_error_log.log')

        return wrapper

    return decorator
