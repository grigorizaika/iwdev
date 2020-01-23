from utils.models import Address
from api.serializers import TaskSerializer

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
def create_address(owner, street, house_no, city, district, country, flat_no=None,):
    return Address.objects.create(
        owner=owner,
        street=street,
        house_no=house_no,
        flat_no=flat_no,
        city=city,
        district=district,
        country=country
    )


def create_presigned_post(bucket_name, object_name,
                          fields=None, conditions=None, expiration=3600):
    import boto3
    import logging
    from botocore.exceptions import ClientError
    
    s3_client = boto3.client('s3')

    try:
        response = s3_client.generate_presigned_post(bucket_name,
                                                     object_name,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    return response

def json_list_group_by(group_by_field, json_list):
    distinct_group_by_field_values = []
    grouped = {}
    
    for item in json_list:
        if not group_by_field in item:
            print('field', group_by_field, 'is not present in a json object')
            continue

        key = str(item[group_by_field])

        try:
            grouped[key].append(item)
        except KeyError:
            grouped[key] = [item]

    return grouped


def bulk_create_tasks(json_task_list, order_id=None):
    full_response = []
    
    for task_json in json_task_list:
        
        if 'order' not in task_json:
            task_json['order'] = order_id

        if not task_json.get('order') == order_id and order_id is not None:
            full_response.append('Task order ID doesn\'t match the one specified in the keyword argument')
            continue

        serializer = TaskSerializer(data=task_json)
        
        if serializer.is_valid():
            task = serializer.save()
            full_response.append('Successfully created task ' + str(task.id) + ' ' + task.name)
        else:
            full_response.append(str(taskSerializer.errors))
    
    return full_response

