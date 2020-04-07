from rest_framework import status
from rest_framework.response import Response

from inworkapi.utils import JSendResponse

def required_body_params(parameter_list=[]):
    def decorator(view_function):
        def wrap(request, *args, **kwargs):
            for param in parameter_list:
                if not param in request.data:
                    response = JSendResponse(
                        status=JSendResponse.FAIL,
                        data={
                            'body': f'Must specify \'{param}\' in the request body'
                        }
                    ).make_json()
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return view_function(request, *args, **kwargs)
        return wrap
    return decorator


def required_kwargs(kwarg_list=[]):
    def decorator(view_function):
        def wrap(request, *args, **kwargs):
            for kwarg in kwarg_list:
                if not kwarg in kwargs:
                    response = JSendResponse(
                        status=JSendResponse.FAIL,
                        data={
                            'url_keyword': f'Must specify \'{kwarg}\' as a url keyword'
                        }
                    ).make_json()
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return view_function(request, *args, **kwargs)
        return wrap
    return decorator


def admin_body_params(parameter_list=[]):
    def decorator(view_function):
        def wrap(request, *args, **kwargs):
            for param in parameter_list:
                if param in request.data and not request.user.is_administrator():
                    response = JSendResponse(
                        status=JSendResponse.FAIL,
                        data={
                            param: f'Only an administrator can set \'{param}\' field'
                        }
                    ).make_json()
                    return Response(response, status=status.HTTP_403_BAD_REQUEST)
            return view_function(request, *args, **kwargs)
        return wrap
    return decorator
