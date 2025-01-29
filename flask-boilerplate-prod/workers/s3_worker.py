"""Contains methods and logic to upload files to s3 bucket."""
import datetime
import os
import traceback

from app import config_data
from app import logger
from app import S3_RESOURCE
from app.helpers.constants import TimeInSeconds
from magic import Magic


def upload_file_and_get_object_details(file_obj, temp_path=None):
    """This method will upload file to bitbucket and return file details."""
    try:
        bucket = config_data['AWS']['S3_BUCKET']
        folder = 'media/'  # create subfolders in media for better management of files

        extension = file_obj.filename.split('.')[1]
        name = file_obj.filename.split('.')[0]
        file_name = name.replace(' ', '_') + '_' + str(datetime.datetime.now().timestamp()).replace('.',  # type: ignore  # noqa: FKA100
                                                                                                    '') + '.' + extension
        if temp_path is None:
            temp_path = os.path.join(config_data['UPLOAD_FOLDER'], file_obj.filename)  # type: ignore  # noqa: FKA100
            file_obj.save(temp_path)
        size = os.stat(temp_path).st_size
        S3_RESOURCE.Bucket(bucket).upload_file(temp_path, f'{folder}{file_name}', ExtraArgs={  # type: ignore  # noqa: FKA100
            'ACL': 'public-read', 'ContentType': Magic(mime=True).from_file(temp_path)})

        os.remove(temp_path)
        return file_name, f'{folder}{file_name}', size

    except Exception as e:  # type: ignore  # noqa: F841
        logger.error(traceback.format_exc())
        return '', '', 0


def delete_file_from_bucket(key):
    """This method is used to delete files from bucket with given keu."""
    bucket = config_data['AWS']['S3_BUCKET']

    try:
        s3_object = S3_RESOURCE.Object(bucket, key)  # type: ignore  # noqa: FKA100

        s3_object.delete()

    except Exception as e:
        logger.error('Error while deleting file from bucket: {}'.format(e))
    return


def get_file_size_by_path(path):
    size = os.stat(path).st_size
    size /= 125  # convert from bytes to kilobits
    size_notation = 'kb'
    if size > 1024:
        size /= 1024  # convert from kb to mb
        size_notation = 'mb'
    size = str(size) + size_notation
    return size


def get_presigned_url(path: str) -> str:
    """Generate a presigned URL to share for S3 object.

        :Bucket: S3 bucket name.
        :Key: Path where file is saved.
        :ExpiresIn: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns Blank String.
        """
    if path is None:
        return ''
    else:
        bucket_name = config_data['AWS']['S3_BUCKET']
        try:
            response = S3_RESOURCE.meta.client.generate_presigned_url('get_object',
                                                                      Params={'Bucket': bucket_name,
                                                                              'Key': path},
                                                                      ExpiresIn=TimeInSeconds.TWO_DAYS.value)
            return response
        except Exception as error:
            logger.error(
                'Error while generating pre-signed url for : {}'.format(path))
            logger.error(
                error
            )
            return ''
