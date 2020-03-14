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