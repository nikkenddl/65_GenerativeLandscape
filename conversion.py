def try_get_float(something,raise_if_fail=True,default=0.0):
    try:
        return float(something)
    except:
        if raise_if_fail:
            raise Exception("float conversion failed. input:{}".format(something))
        else:
            return default
    
def try_get_text(something,raise_if_fail=True,default=""):
    try:
        return str(something)
    except:
        if raise_if_fail:
            raise Exception("text conversion failed. input:{}".format(something))
        else:
            return default
    
def try_get_int(something,raise_if_fail=True,default=None):
    try:
        return int(something)
    except:
        if raise_if_fail:
            raise Exception("int conversion failed. input:{}".format(something))
        else:
            return default
    
def try_convert_strbool_to_bool(text,raise_if_fail=True,default=False):
    if not isinstance(text,str): raise Exception("Input must be text")
    lower = text.lower()
    if lower=='true' or lower=='1':
        return True
    elif lower=='false' or lower=='0':
        return False
    else:
        if raise_if_fail:
            raise Exception("input text must be true/1 or false/0 (case ignored). input:{}".format(text))
        else:
            return default