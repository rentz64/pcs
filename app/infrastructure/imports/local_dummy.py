from app.domain.imports import ExternalAccount, ExternalSource, ImportedContent, ImportJob


class LocalDummyImportAdapter:
    def list_available_content_types(self) -> tuple[str, ...]:
        return ("document", "note")

    def authenticate(self, account: ExternalAccount) -> bool:
        return True

    def test_connection(self, account: ExternalAccount) -> bool:
        return True

    def import_content(self, source: ExternalSource, account: ExternalAccount, job: ImportJob) -> list[ImportedContent]:
        return [
            ImportedContent(
                external_content_id="local-note-1",
                external_content_type="note",
                title="Imported Local Note",
                body="Imported local note body",
                summary="Imported local note",
                tags="imported,note",
                source_url="local://note/1",
            )
        ]
