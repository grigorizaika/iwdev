from django.db import models
from rest_framework import exceptions

from inworkapi.utils import S3Helper


class Address(models.Model):
    owner = models.ForeignKey(
        'utils.AddressOwner',
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    street = models.CharField(max_length=40)
    house_no = models.CharField(max_length=10)
    flat_no = models.CharField(max_length=40, blank=True, null=True)
    city = models.CharField(max_length=40)
    district = models.CharField(max_length=40)
    country = models.CharField(max_length=40)
    postal_code = models.CharField(max_length=12, default='00-001')

    def get_owner_instance(self):
        if self.owner:
            return self.owner.get_owner_instance()
        else:
            return None

    def __str__(self):
        flat_no = ("/" + str(self.flat_no)) if self.flat_no else ''
        return (f'{self.house_no} {flat_no}, \
                {self.street}, {self.city}, \
                {self.district} {self.country}')

    class Meta:
        verbose_name_plural = "Addresses"


# TODO:
# EITHER rename AddressOwner to MultipleAddressOwner,
# and make changes in models accordingly,
# OR make everyone who can have an address an address owner
class AddressOwner(models.Model):

    def get_owner_instance(self):
        # Search a list of all classes that are address owners
        # TODO: so far, this is implemented on the assumption that
        # all one to one relations with this model are address owners
        owner_instance_models = [
            field.related_model for field in self._meta.get_fields()
            if field.__class__ is models.fields.reverse_related.OneToOneRel
        ]

        owner_instance = None

        for owner_instance_model in owner_instance_models:
            try:
                owner_instance = (owner_instance_model.objects
                                  .get(address_owner=self.id))
            except owner_instance_model.DoesNotExist:
                continue

        try:
            if not owner_instance:
                print("""Neither the of owner instance classes has an instance
                        that corresponds to the owner id """ + str(self.id))
                # TODO: there may be a problem with loose address_owners
                return None
        except UnboundLocalError:
            raise exceptions.NotFound(
                detail='''Address owner instance not found \
                    for this address owner2''')

        return owner_instance

    def __str__(self):
        return f'AO_{self.id} {self.get_owner_instance()}'


class CustomFile(models.Model):
    owner = models.ForeignKey(
        'utils.FileOwner',
        on_delete=models.CASCADE,
        null=False,
        blank=False)
    name = models.CharField(max_length=191)
    location = models.URLField(max_length=300)
    date_created = models.DateTimeField(auto_now_add=True)

    def get_owner_instance(self):
        if self.owner:
            return self.owner.get_owner_instance()
        else:
            return None

    def get_s3_key(self):
        location = next(location_string
                        for location_string, model_class_name
                        in S3Helper.KEY_TO_MODEL_MAPPING
                        if model_class_name == self.__class__.__name)
        instance_id = self.get_owner_instance().id
        file_name = self.name

        return location + '/' + instance_id + '/' + file_name

    def delete_from_s3(self):
        file_key = self.get_s3_key()
        # TODO: use delete_file instead of delete_files?
        S3Helper.delete_files(file_keys_list=[file_key])

    def __str__(self):
        return f'{self.name} {self.location}'

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"


class FileOwner(models.Model):

    def get_owner_instance(self):
        # Search a list of all classes that are address owners
        # TODO: so far, this is implemented on the assumption that
        # all one to one relations with this model are address owners
        owner_instance_models = [field.related_model
                                 for field in self._meta.get_fields()
                                 if field.__class__
                                 is models.fields.reverse_related.OneToOneRel]

        owner_instance = None

        for owner_instance_model in owner_instance_models:
            try:
                owner_instance = (owner_instance_model.objects
                                  .get(file_owner=self.id))
            except owner_instance_model.DoesNotExist:
                continue

        try:
            if not owner_instance:
                print(f"""Neither the of owner instance classes has an instance
                        that corresponds to the owner id {self.id}""")
                # TODO: there may be a problem with loose file_owners
                return None
        except UnboundLocalError:
            raise exceptions.NotFound(
                detail="File owner instance not found for this address owner")

        return owner_instance

    def get_files(self):
        return CustomFile.objects.filter(owner=self.id)

    def wipe_s3_files(self):
        file_keys = [
            f.get_s3_key()
            for f in self.get_files()]
        S3Helper.delete_files(file_keys_list=file_keys)

    def __str__(self):
        return f'FO_{self.id} {self.get_owner_instance()}'

    @staticmethod
    def delete_cleanup(sender, instance, *args, **kwargs):
        instance.wipe_s3_files()


models.signals.post_delete.connect(FileOwner.delete_cleanup, sender=FileOwner)
