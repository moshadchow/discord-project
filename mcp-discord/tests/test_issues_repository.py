import unittest

from discord_mcp.issues_repository import IssueAttachment, serialize_attachments


class AttachmentSerializationTests(unittest.TestCase):
    def test_serialize_attachments_returns_json_compatible_metadata(self):
        attachments = (
            IssueAttachment(
                attachment_name="screenshot",
                original_file_name="screenshot.png",
                file_extension="png",
                url="https://cdn.discordapp.com/attachments/1/screenshot.png",
                content_type="image/png",
                size_bytes=2048,
            ),
            IssueAttachment(
                attachment_name="archive",
                original_file_name="archive.zip",
                file_extension="zip",
                url="https://cdn.discordapp.com/attachments/1/archive.zip",
                content_type=None,
                size_bytes=4096,
            ),
        )

        self.assertEqual(
            serialize_attachments(attachments),
            [
                {
                    "attachment_name": "screenshot",
                    "original_file_name": "screenshot.png",
                    "file_extension": "png",
                    "url": "https://cdn.discordapp.com/attachments/1/screenshot.png",
                    "content_type": "image/png",
                    "size_bytes": 2048,
                },
                {
                    "attachment_name": "archive",
                    "original_file_name": "archive.zip",
                    "file_extension": "zip",
                    "url": "https://cdn.discordapp.com/attachments/1/archive.zip",
                    "content_type": None,
                    "size_bytes": 4096,
                },
            ],
        )

    def test_serialize_attachments_handles_empty_collection(self):
        self.assertEqual(serialize_attachments(()), [])
