from django.urls import path
from django.conf.urls import url, include

from .views import (
    OrderView, TaskView, accept_hours_worked
)



app_name = 'orders'

order_list = OrderView.as_view()
task_list = TaskView.as_view()


urlpatterns = [
    url(r'orders/?$', order_list),
    path('orders/<int:id>/', order_list),
    
    url(r'tasks/?$', task_list),
    path('tasks/<int:id>/', task_list),
    url(r'tasks/accept_hours/?$', accept_hours_worked),
    
]