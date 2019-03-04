def serialize(obj):
    pars = {}
    for field in  obj.__class__._meta.fields:
        pars.update((field.name, obj.getatr[field.name]))
    return pars
