from io import StringIO

from django.core.management import call_command

from media_library.models import Image
from music.models import Album, Song, Track
from payload_migration.audit import audit_snapshot
from payload_migration.client import read_json
from payload_migration.importers import PayloadSnapshotImporter
from payload_migration.lexical import LexicalConverter
from sites_core.models import Site
from writing.models import Article, Book


def lexical_doc(*children):
    return {"root": {"children": list(children)}}


def paragraph(*children):
    return {"type": "paragraph", "children": list(children)}


def text(value, format_value=0):
    return {"type": "text", "text": value, "format": format_value}


def test_lexical_converter_renders_common_nodes_and_records_unknown():
    converter = LexicalConverter()
    html = converter.convert(
        lexical_doc(
            paragraph(
                text("Hello ", 1),
                {"type": "link", "fields": {"url": "https://example.com"}, "children": [text("link")]},
                {"type": "linebreak"},
                text("world", 2),
            ),
            {"type": "widget", "children": [text("fallback")]},
        ),
        collection="posts",
        document_id=1,
        field_name="content",
    )

    assert html == '<p><strong>Hello </strong><a href="https://example.com">link</a><br><em>world</em></p>fallback'
    assert converter.unknown_as_dicts() == [
        {
            "collection": "posts",
            "document_id": 1,
            "field_name": "content",
            "node_type": "widget",
            "excerpt": {"type": "widget"},
        }
    ]


def test_snapshot_importer_imports_representative_pilot_subset(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    cover = Image.objects.create(site=site, title="Cover", payload_id=10)
    snapshot = {
        "posts": [
            {
                "id": 1,
                "title": "Post",
                "slug": "post",
                "content": lexical_doc(paragraph(text("Post body"))),
                "contentPlain": "Post body",
                "categories": "news",
                "featuredImage": 10,
                "_status": "published",
            }
        ],
        "albums": [
            {
                "id": 2,
                "title": "Album",
                "slug": "album",
                "artist": "Kent",
                "category": "commercial",
                "description": lexical_doc(paragraph(text("Album body"))),
                "coverImage": 10,
                "_status": "published",
            }
        ],
        "chansons": [
            {
                "id": 3,
                "title": "Song",
                "slug": "song",
                "lyrics": lexical_doc(paragraph(text("Lyrics"))),
                "_status": "published",
            }
        ],
        "album-tracks": [
            {
                "id": 4,
                "displayTitle": "Album - Song",
                "album": 2,
                "chanson": 3,
                "discNumber": 1,
                "trackNumber": 1,
                "versionType": "studio",
            }
        ],
        "livres": [
            {
                "id": 5,
                "title": "Illustrated",
                "slug": "illustrated",
                "category": "illustrated",
                "description": lexical_doc(paragraph(text("Book body"))),
                "coverImage": 10,
                "_status": "published",
            }
        ],
    }

    counts = PayloadSnapshotImporter(site=site).import_snapshot(snapshot, max_docs=3)

    assert counts["posts"] == 1
    assert Article.objects.get(payload_id=1).content_html == "<p>Post body</p>"
    assert Album.objects.get(payload_id=2).cover_image == cover
    assert Song.objects.get(payload_id=3).lyrics_html == "<p>Lyrics</p>"
    assert Track.objects.get(payload_id=4).album.payload_id == 2
    assert Book.objects.get(payload_id=5).show_on_drawings_page is True


def test_export_payload_snapshot_writes_collection_files(tmp_path, monkeypatch):
    def fake_fetch_collection(collection, **kwargs):
        return {"docs": [{"id": 1, "collection": collection}], "totalDocs": 1}

    monkeypatch.setattr(
        "payload_migration.management.commands.export_payload_snapshot.fetch_payload_collection",
        fake_fetch_collection,
    )
    stdout = StringIO()

    call_command(
        "export_payload_snapshot",
        "--collection",
        "posts",
        "--skip-globals",
        "--output-dir",
        tmp_path,
        stdout=stdout,
    )

    assert read_json(tmp_path / "posts.json")["docs"] == [{"id": 1, "collection": "posts"}]
    assert "Exported posts: 1 docs" in stdout.getvalue()


def test_import_payload_snapshot_logs_unknown_lexical_nodes(tmp_path, db):
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    (tmp_path / "posts.json").write_text(
        """
        {
          "docs": [
            {
              "id": 1,
              "title": "Post",
              "slug": "post",
              "content": {
                "root": {
                  "children": [
                    {"type": "unknownBlock", "children": [{"type": "text", "text": "fallback"}]}
                  ]
                }
              }
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    log_dir = tmp_path / "logs"

    call_command(
        "import_payload_snapshot",
        "--site",
        "kent",
        "--input-dir",
        tmp_path,
        "--log-dir",
        log_dir,
    )

    unknown = read_json(log_dir / "unknown_lexical_nodes.json")
    assert unknown[0]["node_type"] == "unknownBlock"
    assert Article.objects.get(payload_id=1).content_html == "fallback"


def test_audit_payload_import_reports_counts_and_unresolved_refs(tmp_path, db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Album.objects.create(site=site, title="Album", slug="album", payload_id=2)
    Song.objects.create(site=site, title="Song", slug="song", payload_id=3)
    Track.objects.create(
        album=Album.objects.get(payload_id=2),
        song=Song.objects.get(payload_id=3),
        track_number=1,
        payload_id=4,
    )
    (tmp_path / "albums.json").write_text(
        '{"docs":[{"id":2,"title":"Album"},{"id":999,"title":"Missing"}]}',
        encoding="utf-8",
    )
    (tmp_path / "album-tracks.json").write_text(
        '{"docs":[{"id":4,"album":2,"chanson":3},{"id":5,"album":999,"chanson":888}]}',
        encoding="utf-8",
    )
    (tmp_path / "posts.json").write_text(
        '{"docs":[{"id":10,"featuredImage":77}]}',
        encoding="utf-8",
    )

    report = audit_snapshot(site=site, input_dir=tmp_path, log_dir=tmp_path / "logs")

    assert {"collection": "albums", "snapshot": 2, "imported": 1} in report["counts"]
    assert {"collection": "album-tracks", "snapshot": 2, "imported": 1} in report["counts"]
    assert report["unresolved_tracks"] == [
        {"document_id": 5, "field": "album", "payload_id": 999},
        {"document_id": 5, "field": "chanson", "payload_id": 888},
    ]
    assert report["unresolved_media"] == [
        {
            "collection": "posts",
            "document_id": 10,
            "field": "featuredImage",
            "media_payload_id": 77,
        }
    ]


def test_audit_payload_import_command_outputs_summary(tmp_path, db):
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    (tmp_path / "posts.json").write_text('{"docs":[{"id":1}]}', encoding="utf-8")
    stdout = StringIO()

    call_command("audit_payload_import", "--site", "kent", "--input-dir", tmp_path, stdout=stdout)

    assert "posts: imported 0 / snapshot 1" in stdout.getvalue()
    assert "Unknown Lexical nodes: 0" in stdout.getvalue()


def test_write_migration_report_command_outputs_json(tmp_path, db):
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    (tmp_path / "posts.json").write_text('{"docs":[{"id":1}]}', encoding="utf-8")
    output = tmp_path / "report.json"

    call_command(
        "write_migration_report",
        "--site",
        "kent",
        "--input-dir",
        tmp_path,
        "--output",
        output,
    )

    report = read_json(output)
    assert report["counts"] == [{"collection": "posts", "snapshot": 1, "imported": 0}]
