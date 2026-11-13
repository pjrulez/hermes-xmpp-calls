Title: Question: images/documents to the agent, and OMEMO for files and voice (XEP-0454)

Two related questions before I write any code. I would like to know whether you want these in the plugin, and in what shape.

## 1. Receiving pictures, documents and spreadsheets in the agent

As far as I can tell from `adapter.py` on `main`, the plugin hands the agent two things: text, and voice notes (an audio attachment is downloaded, checked, put in Hermes' audio cache and set as `media_urls` / `media_types` on a `VOICE` event, so the `stt` provider transcribes it). Anything else a person sends (a photo, a PDF, a Word or Excel file) arrives as the URL in the message text. The agent cannot look at it.

I would like to be able to send the agent pictures, `.docx` and `.xlsx` files (mostly pictures, Word documents and spreadsheets) and have it work with them. Hermes core already has the pieces: `MessageType.PHOTO` / `DOCUMENT`, and the cache helpers `cache_image_from_bytes_async`, `cache_document_from_bytes_async` (and `cache_media_bytes_async`), with the `gateway.max_inbound_media_bytes` cap.

What I have in mind, reusing what the voice path already does (authorisation before any fetch, `https` and `aesgcm` only, SSRF checks through Hermes for untrusted hosts, size cap while streaming, bodies carrying keys never reach the model):

- a message with exactly one attachment (OOB or XEP-0447 SFS, with or without a caption) whose type is an image or a document becomes a `PHOTO` or `DOCUMENT` event with the file cached and the caption as text;
- an allow-list of types (images; PDF, `.docx`, `.xlsx`, `.pptx`, `.txt`, `.md`, `.csv`, `.json`), nothing else downloaded;
- a config switch, off or on by default (your call), plus the existing size cap.

Questions:

1. Is this in scope for the plugin, or do you prefer it stays text and voice only?
2. If yes: should it be on by default? And is the allow-list above right, or should it be narrower or configurable?
3. Would you prefer it as one PR, or images first and documents after?

## 2. OMEMO for files and voice: XEP-0454 (OMEMO Media Sharing)

Today, with OMEMO on, only the message text is encrypted. Outgoing voice notes, images and files are uploaded in the clear (XEP-0363) and sent as a link; for voice the stanza also carries a plain XEP-0447 file description. I believe that is simply what the adapter does and not a configuration issue, but please correct me if I misread it.

The plugin already receives encrypted media: `aesgcm://` links are decrypted in `_parse_aesgcm_url` / `_aesgcm_decrypt`. Only sending is missing. XEP-0454 would work like this: encrypt the file with AES-256-GCM using a random key and IV, upload the ciphertext, and put an `aesgcm://host/path#<iv><key>` link inside the OMEMO-encrypted message. Conversations and Dino support it.

Open points I would test before any PR: how Conversations, Dino and Monal play an encrypted voice note (and whether the XEP-0447 description should be kept), file size limits on the upload service (the ciphertext is 16 bytes larger), and what to do when OMEMO is on but encryption for a peer fails (today the adapter falls back to plaintext for text; for media I would rather refuse than leak a file).

Questions:

1. Do you want encrypted media sending in the plugin?
2. Should it be automatic whenever the text of that conversation would be OMEMO-encrypted, or behind an option?
3. For a failed encryption: send nothing and report an error, or fall back to the plain upload as for text?

I can send small PRs for either. If you would rather not take them, that is fine too; I keep them in my own fork.
