from django.http import HttpRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET
from WorldIT.decorators import required_type

# Create your views here.
@require_GET
@required_type(["student", "mentor", "manager", "admin"])
def render_all_modules(request: HttpRequest):
    
    return render(
        request=request, 
        template_name="english/all_modules.html"
    )

@require_GET
@required_type(["student", "mentor", "manager", "admin"])
def render_module(request: HttpRequest, module_id: int):
    
    return render(
        request=request, 
        template_name="english/module.html"
    )
