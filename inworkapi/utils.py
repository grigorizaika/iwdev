import boto3
import logging

from botocore.config import Config
from botocore.exceptions import ClientError
from django_cognito_jwt import JSONWebTokenAuthentication
from django.conf import settings


class JSendResponse:
    """
        Reseponse with a structure described in
        https://github.com/omniti-labs/jsend
    """
    SUCCESS = 'success'
    FAIL = 'fail'
    ERROR = 'error'
    statuses = [SUCCESS, FAIL, ERROR]

    def __init__(self, status, data=None, message=None):

        if status not in self.statuses:
            raise ValueError(
                'Status must be one of these values: {}'
                .format(self.statuses))

        self._status = status

        if not status == self.ERROR and message:
            raise ValueError("""Only a response with a status \
                \'error\' can have \'message\' attribute """)

        self._data = data
        self._message = message

    @property
    def status(self):
        return self._status

    @property
    def data(self):
        return self._data

    @property
    def message(self):
        return self._message

    @data.setter
    def data(self, value):
        self._data = value

    @message.setter
    def message(self, value):
        if self.status == self.ERROR:
            self._message = value
        else:
            raise ValueError("""Can only set a mesage on a response \
                              with an \'error\' status"""
                             .format(self._status))

    def make_json(self):
        response_dict = {}
        response_dict['status'] = self._status

        if self.data:
            response_dict['data'] = self.data
        elif self.status == self.FAIL or self.status == self.SUCCESS:
            response_dict['data'] = None

        if self.message:
            response_dict['message'] = self._message
        elif self.status == self.ERROR:
            response_dict['message'] = None

        # TODO: sholdn't it be "return json.dumps(response_dict, indent=4)"?
        # that way it is displayed without formatting in Postman
        return response_dict


class CognitoHelper:

    @staticmethod
    def get_client():
        return boto3.client(
            'cognito-idp',
            region_name=settings.COGNITO_AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

    @staticmethod
    def get_cognito_user(email):
        return (CognitoHelper.get_client()
                .admin_get_user(
                    UserPoolId=settings.COGNITO_USER_POOL_ID,
                    Username=email))

    @staticmethod
    def assertCognitoUserExists(email):
        try:
            return CognitoHelper.get_cognito_user(email)
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                raise AssertionError(
                    f"""No {email} in \
                        {settings.COGNITO_USER_POOL_ID} user pool.""")
            else:
                raise e

    @staticmethod
    def assertCognitoUserDoesntExist(email):
        try:
            CognitoHelper.get_cognito_user(email)
            raise AssertionError(
                f"""{email} exists in \
                    {settings.COGNITO_USER_POOL_ID} user pool.""")
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return
            else:
                raise e


class S3Helper:

    MAIN_BUCKET_NAME = 'inwork-bucket'

    KEY_TO_MODEL_MAPPING = {
        'clients': 'Client',
        'orders': 'Order',
        'tasks': 'Task',
        'users': 'User',
    }

    @staticmethod
    def get_client():
        return boto3.client(
            's3',
            region_name=settings.COGNITO_AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
        )

    @staticmethod
    def create_presigned_post(object_name, bucket_name=MAIN_BUCKET_NAME,
                              fields=None, conditions=None, expiration=3600):
        """
        NOTE:
        Using POST yields 405 (Method Not Allowed)
        when making a request to the generated URL.
        Substituted it with the function below,
        which generates a pre-signed PUT.
        TODO:
        Didn't find the answer neither on forums,
        nor at stackoverflow. Further investigate the issue.
        """

        s3_client = S3Helper.get_client()

        try:
            return s3_client.generate_presigned_post(
                bucket_name,
                object_name,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expiration
            )
        except ClientError as e:
            logging.error(e)
            return None

    def create_presigned_put(object_name, bucket_name=MAIN_BUCKET_NAME,
                             fields=None, conditions=None, expiration=3600):
        s3_client = S3Helper.get_client()

        try:
            return s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': object_name,
                },
                HttpMethod="PUT",
            )
        except ClientError as e:
            print(e)

    @staticmethod
    def delete_files(file_keys_list, bucket_name=MAIN_BUCKET_NAME):
        objects_aws_formatted = [
            {'Key': file_key}
            for file_key in file_keys_list]

        try:
            S3Helper.get_client().delete_objects(
                Bucket=bucket_name,
                Delete={
                    'Objects': objects_aws_formatted
                })
        except ClientError as e:
            print(e)

    @staticmethod
    def delete_all_with_prefix(prefix, bucket_name=MAIN_BUCKET_NAME):
        bucket = boto3.resource('s3').Bucket(bucket_name)

        delete_response = bucket.objects.filter(Prefix=prefix).delete()

        return delete_response


class TokenHelper:

    @staticmethod
    def get_tokens(username, password):

        client = CognitoHelper.get_client()

        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
            },
            ClientId=settings.COGNITO_APP_CLIENT_ID,
        )

        return response

    @staticmethod
    def refresh_id_token(refresh_token):

        client = CognitoHelper.get_client()

        response = client.initiate_auth(
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token
            },
            ClientId=settings.COGNITO_APP_CLIENT_ID,
        )

        return response

    @staticmethod
    def get_user_by_token(request, token):
        auth = JSONWebTokenAuthentication()
        jwt_payload = auth.get_token_validator(request).validate(token)
        user = (auth.get_user_model().objects
                .get_or_create_for_cognito(jwt_payload))

        return user
