import random

from utils.models import Address
from orders.serializers import TaskSerializer
from orders.models import Order


def slice_fields(key_list, l):
    l_sliced = []
    for d in l:
        d_sliced = {}
        for k in d:
            if k in key_list:
                d_sliced[k] = d[k]
        l_sliced.append(d_sliced)
    return l_sliced


# TODO: Probably want to use serializers here
def create_address(owner, street, house_no,
                   city, district, country,
                   flat_no=None,):
    return Address.objects.create(
        owner=owner,
        street=street,
        house_no=house_no,
        flat_no=flat_no,
        city=city,
        district=district,
        country=country
    )


def json_list_group_by(group_by_field, json_list):
    grouped = {}

    for item in json_list:
        if group_by_field not in item:
            print('field', group_by_field, 'is not present in a json object')
            continue

        key = str(item[group_by_field])

        try:
            grouped[key].append(item)
        except KeyError:
            grouped[key] = [item]

    return grouped


def bulk_create_tasks(json_task_list, user, order_id=None):
    full_response = []

    for task_json in json_task_list:

        if 'order_id' not in task_json:
            task_json['order_id'] = order_id

        try:
            order = Order.objects.get(id=task_json['order_id'])
        except Order.DoesNotExist:
            full_response.append(
                                 'Order'
                                 + str(task_json['order_id'])
                                 + ' does not exist.')
            continue

        if not order.client.company == user.company:
            full_response.append(
                """Can\'t create a task for an order \
                    that doesn\'t belong to the request user\'s company""")
            continue

        if (not task_json.get('order_id') == order_id
                and order_id is not None):
            full_response.append(
                """Task order ID doesn\'t match the \
                    one specified in the keyword argument""")
            continue

        serializer = TaskSerializer(data=task_json)

        if serializer.is_valid():
            task = serializer.save()
            full_response.append(
                f'Successfully created task {task.id} {task.name}')
        else:
            full_response.append(str(serializer.errors))

    return full_response


def generate_temporary_password(password_length=10):
    charachters = '1234567890ABCDEF'
    generated_password = ''
    for i in range(0, password_length):
        generated_password += random.choice(charachters)
    return generated_password
