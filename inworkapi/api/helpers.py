from utils.models import Address


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

