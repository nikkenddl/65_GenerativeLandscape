def try_get_float(something,default=0.0):
    if something is None: return default
    try:
        return float(something)
    except:
        return default
    
def try_get_text(something,default=""):
    if something is None: return default
    try:
        return str(something)
    except:
        return default
    
def try_get_int(something,default=""):
    if something is None: return default
    try:
        return int(something)
    except:
        return default