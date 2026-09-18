from django.shortcuts import redirect
from functools import wraps

def required_type(account_type: str | list):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                for type in getattr(request.user, "account_types", []):
                    if type in account_type:
                        return view_func(request, *args, **kwargs)
            
            return redirect('main') 
        return _wrapped_view
    return decorator