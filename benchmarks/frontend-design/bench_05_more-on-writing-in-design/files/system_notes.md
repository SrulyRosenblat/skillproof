# Eng notes — Shared Folders (sprint 14)

Internal name: `sync_group`. Each shared folder is a row in the `sync_groups` table,
keyed by `sync_group_id`.

## Ticket ENG-482: Archive shared folder
Summary: Let a folder owner archive a shared folder from the UI.
Implementation: `POST /api/v2/sync-groups/{id}/deactivate` sets `sync_groups.status =
'archived'` and stops the sync cron for that group. Code comments refer to this as a
"soft-delete" of the sync_group row (files are kept, the folder just stops syncing).
Front-end needs a button that calls this endpoint, plus something shown after it
succeeds.

## Ticket ENG-491: Remove a team member from a folder
Summary: Let a folder owner remove someone else's access to a shared folder.
Implementation: `DELETE /api/v2/sync-groups/{id}/members/{user_id}`. Internally this
is called `revoke_membership`. On success the API returns `204 No Content`. Front-end
needs a button that calls this endpoint, plus something shown after it succeeds.

## Ticket ENG-503: Upload size limit
Summary: Reject uploads that exceed the configured max size.
Implementation: the upload endpoint checks `file.size > MAX_UPLOAD_BYTES` (see
limits.json) before accepting the multipart payload, and returns
`413 Payload Too Large` with an error body `{"error": "payload_too_large"}` if the
check fails. Front-end needs to catch this response and show something to the person
uploading instead of the raw error.

## Ticket ENG-511: Empty shared folder
Summary: `GET /api/v2/sync-groups/{id}/files` returns `{"files": []}` when nothing has
been uploaded to the folder yet. Front-end currently renders a blank list in this case
and needs a placeholder state instead.
