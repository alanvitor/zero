"""B2 file back-end.
The lifecycle settings on the bucket must be configured to
'keep only the last version.
"""
from io import BytesIO
from b2.api import B2Api
from b2.bucket import Bucket
from b2.account_info.in_memory import InMemoryAccountInfo
from b2.download_dest import DownloadDestBytes


class FileAPI:

    def __init__(self, file_info_store, account_id, application_key, bucket_id):
        account_info = InMemoryAccountInfo()
        self.api = B2Api(account_info)
        self.api.authorize_account("production", account_id, application_key)
        self.bucket_api = Bucket(self.api, bucket_id)
        self.file_info_store = file_info_store

    def _encode_identifier(self, identifier):
        return identifier[1:]

    def _decode_identifier(self, identifier):
        return "/" + identifier

    def upload(self, file, identifier):
        data = file.read()
        file_info = self.bucket_api.upload_bytes(
            data, self._encode_identifier(identifier)
        )
        print("trying to set file id")
        self.file_info_store.set_file_id(
            identifier, file_info.as_dict().get("fileId")
        )

    def delete(self, identifier):
        file_id = self.file_info_store.get_file_id(identifier)
        if not file_id:
            # No file ID means file was never synched to remote
            print(
                f"Not deleting {identifier} because no file_id in file info store"
                f"Maybe file had never been synched to remote"
            )
            return
        self.bucket_api.delete_file_version(
            file_id, self._encode_identifier(identifier)
        )
        self.file_info_store.remove_entry(identifier)

    def download(self, identifier):
        download_dest = DownloadDestBytes()
        file_id = self.file_info_store.get_file_id(identifier)
        self.bucket_api.download_file_by_id(file_id, download_dest)
        return BytesIO(download_dest.get_bytes_written())
