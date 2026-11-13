Title: Question: attachments to the agent (images, PDFs, documents, ...) and OMEMO for files and voice (XEP-0454)

Two related questions about what the plugin does with files. I am asking before writing any code, because the answers decide whether and how this should be done.

## 1. Which attachments reach the agent today, and should more of them?

As far as I can tell from `adapter.py` on `main`, the agent receives two kinds of input over XMPP: text, and voice notes. A voice note (an audio attachment as OOB, XEP-0447 SFS, or an OMEMO `aesgcm://` link, with no caption) is downloaded with authorisation, scheme, SSRF, size and type checks, put in Hermes' audio cache and delivered as a `VOICE` event with `media_urls` / `media_types`, so the `stt` provider can transcribe it.

Everything else a person sends is, as far as I can tell, not processed. It reaches the agent only as the URL inside the message text. I tried this with an image: the agent answered that it could not open the URL. That is expected, because the agent has no way to fetch it. Not handled today, as far as I can tell:

- **Images** (jpg, png, webp, gif, heic): the agent cannot look at them, so no "what is in this picture", screenshot reading, OCR or diagrams.
- **PDFs**: no reading a PDF for context.
- **Office documents and spreadsheets**: `.docx`, `.xlsx`, `.pptx`, and the OpenDocument equivalents.
- **Text and data files**: `.txt`, `.md`, `.csv`, `.json`, logs, source files.
- **Archives** (`.zip` and similar), **video** (`.mp4`, `.webm`), and **audio that is not a lone voice note** (a music file, or a voice note sent with a caption).
- **Several attachments in one message**, and an attachment together with a caption.
- **Other XMPP content**: shared locations (XEP-0080 / `geo:` URIs), contact cards.
- **Encrypted attachments** other than a lone voice note: an OMEMO `aesgcm://` image or file is not decrypted (only the voice path knows `aesgcm://`).

Hermes core already has the receiving side: `MessageType.PHOTO` and `DOCUMENT`, the cache helpers `cache_image_from_bytes_async`, `cache_document_from_bytes_async` and `cache_media_bytes_async`, and the `gateway.max_inbound_media_bytes` cap. The plugin would only need to do for these types what it does for voice: validate, download, cache, and hand the event over with the caption as text.

What I would like is for an allowed user to send the agent a picture, a PDF or a spreadsheet, with a caption such as "what is this" or "use this as context", and have the agent work with it, securely.

Questions:

1. Is this in scope for the plugin, or do you prefer text and voice only?
2. If yes, which types first? My own priority is images, PDFs, Word documents and spreadsheets, then plain text and data files. Should the set be a fixed allow-list or configurable?
3. On or off by default? Opt-in per profile seems safer, since the agent may run tools on what it receives.
4. The same download rules as voice (authorisation before any fetch, `https` and `aesgcm` only, SSRF checks through Hermes for untrusted hosts, size cap while streaming) plus a type check on the content and not only on the extension. Is that the right baseline, or do you want more (a lower default size cap, a per-user limit, an explicit allow-list of upload hosts)?
5. A document is untrusted input that the agent will read, so it is also a prompt-injection channel. Should the plugin mark attachment text as untrusted content, or leave that to Hermes core?
6. Images need a vision-capable model and documents need extraction (PDF text, `.docx` and `.xlsx` parsing). Should the plugin only deliver the cached file with the right type and leave interpretation to Hermes core and the agent's tools, or should it do any conversion itself? My preference is the former.
7. How should unsupported or too large files be answered? Today they are silent. A short reply to the sender ("I can't read .zip files") seems more useful.
8. Should the same apply in group chats (MUC), or direct messages only?
9. The other direction, files the agent sends, works as a link after an XEP-0363 upload. Is there anything there you would want changed?

## 2. OMEMO for files and voice: XEP-0454 (OMEMO Media Sharing)

With OMEMO on, only the message text is encrypted today. Outgoing voice notes, images and files are uploaded unencrypted (XEP-0363) and sent as a link; for voice the stanza also carries a plain XEP-0447 file description. I believe that is simply what the adapter does and not a configuration issue, but please correct me if I misread it.

The plugin already receives encrypted voice notes (`_parse_aesgcm_url`, `_aesgcm_decrypt`). Only sending is missing. XEP-0454 works like this: encrypt the file with AES-256-GCM using a random key and IV, upload the ciphertext, and put an `aesgcm://host/path#<iv><key>` link inside the OMEMO-encrypted message. Conversations and Dino support it.

Open points to test before any code: how Conversations, Dino and Monal play an encrypted voice note (and whether the XEP-0447 description should stay), upload size limits (the ciphertext is 16 bytes larger), and the failure case.

Questions:

1. Do you want encrypted media sending in the plugin?
2. Automatic whenever the conversation's text would be OMEMO-encrypted, or behind an option?
3. When encryption for a peer fails: send nothing and report an error, or fall back to the plain upload as the plugin does for text? For files I lean towards refusing.
4. The two parts meet: if encrypted inbound images and documents are supported (last bullet of part 1), the decryption code is shared. Would you rather see them designed together?

Thank you for taking a look. Any of these can be answered with "not in this plugin".
