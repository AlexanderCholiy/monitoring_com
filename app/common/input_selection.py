from argparse import ArgumentTypeError


def input_selection(value: str):
    if value.lower() in ('true', '1', 't', 'y', 'yes'):
        return True
    elif value.lower() in ('false', '0', 'f', 'n', 'no'):
        return False
    else:
        raise ArgumentTypeError('Ожидается True или False.')
