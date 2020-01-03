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
def create_address(street, houseNo, city, district, country, flatNo=None,):
    return Address.objects.create(
        street=street,
        houseNo=houseNo,
        flatNo=flatNo,
        city=city,
        district=district,
        country=country
    )