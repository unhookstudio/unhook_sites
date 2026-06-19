from dataclasses import dataclass
from html import escape
from typing import Any


TEXT_FORMATS = {
    1: ("strong",),
    2: ("em",),
    4: ("s",),
    8: ("u",),
}


@dataclass
class UnknownLexicalNode:
    collection: str
    document_id: Any
    field_name: str
    node_type: str
    excerpt: dict[str, Any]


class LexicalConverter:
    def __init__(self):
        self.unknown_nodes: list[UnknownLexicalNode] = []

    def convert(self, value: dict[str, Any] | None, *, collection: str, document_id: Any, field_name: str) -> str:
        if not value:
            return ""
        root = value.get("root", {})
        return "".join(
            self._render_block(
                child,
                collection=collection,
                document_id=document_id,
                field_name=field_name,
            )
            for child in root.get("children", [])
        )

    def _render_block(self, node: dict[str, Any], *, collection: str, document_id: Any, field_name: str) -> str:
        node_type = node.get("type")
        children = self._render_children(
            node,
            collection=collection,
            document_id=document_id,
            field_name=field_name,
        )
        if node_type == "paragraph":
            return f"<p>{children}</p>"
        if node_type == "heading":
            tag = node.get("tag") or "h2"
            if tag not in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                tag = "h2"
            return f"<{tag}>{children}</{tag}>"
        if node_type == "quote":
            return f"<blockquote>{children}</blockquote>"
        if node_type == "list":
            tag = "ol" if node.get("listType") == "number" else "ul"
            return f"<{tag}>{children}</{tag}>"
        if node_type == "listitem":
            return f"<li>{children}</li>"

        self._record_unknown(collection, document_id, field_name, node)
        return children

    def _render_children(self, node: dict[str, Any], *, collection: str, document_id: Any, field_name: str) -> str:
        return "".join(
            self._render_inline(
                child,
                collection=collection,
                document_id=document_id,
                field_name=field_name,
            )
            for child in node.get("children", [])
        )

    def _render_inline(self, node: dict[str, Any], *, collection: str, document_id: Any, field_name: str) -> str:
        node_type = node.get("type")
        if node_type == "text":
            text = escape(node.get("text") or "")
            for tag in self._tags_for_format(node.get("format") or 0):
                text = f"<{tag}>{text}</{tag}>"
            return text
        if node_type == "linebreak":
            return "<br>"
        if node_type == "link":
            url = escape((node.get("fields") or {}).get("url") or "#", quote=True)
            children = self._render_children(
                node,
                collection=collection,
                document_id=document_id,
                field_name=field_name,
            )
            return f'<a href="{url}">{children}</a>'
        if node_type in {"paragraph", "heading", "quote", "list", "listitem"}:
            return self._render_block(
                node,
                collection=collection,
                document_id=document_id,
                field_name=field_name,
            )

        self._record_unknown(collection, document_id, field_name, node)
        return self._render_children(
            node,
            collection=collection,
            document_id=document_id,
            field_name=field_name,
        )

    def _tags_for_format(self, format_value: int) -> list[str]:
        tags: list[str] = []
        for bit, bit_tags in TEXT_FORMATS.items():
            if format_value & bit:
                tags.extend(bit_tags)
        return tags

    def _record_unknown(self, collection: str, document_id: Any, field_name: str, node: dict[str, Any]) -> None:
        self.unknown_nodes.append(
            UnknownLexicalNode(
                collection=collection,
                document_id=document_id,
                field_name=field_name,
                node_type=node.get("type") or "<missing>",
                excerpt={key: node.get(key) for key in ["type", "tag", "fields"] if key in node},
            )
        )

    def unknown_as_dicts(self) -> list[dict[str, Any]]:
        return [
            {
                "collection": node.collection,
                "document_id": node.document_id,
                "field_name": node.field_name,
                "node_type": node.node_type,
                "excerpt": node.excerpt,
            }
            for node in self.unknown_nodes
        ]
