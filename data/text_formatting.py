# beautifies number for printing
def l1(number) -> str:
    """
    Rounds the number to one decimal place and returns a string.
    """
    return str(round(number, 1))


def l2(number) -> str:
    """
    Rounds the number to two decimal places and returns a string.
    """
    return str(round(number, 2))


def l3(number) -> str:
    """
    Rounds the number to three decimal place and returns a string. Removes the leading 0 if less than 1.
    1.39484 -> 1.395, 0.284532 -> .285
    """
    if number >= 1:
        output = '{0:.3f}'.format(number)
    else:
        output = '{0:.3f}'.format(number)[1:]
    if output == '':
        return '0'
    return output
