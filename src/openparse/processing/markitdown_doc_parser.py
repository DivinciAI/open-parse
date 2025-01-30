from typing import Union, List, Optional, Dict, Tuple
from datetime import date
import logging
from pathlib import Path
from markitdown import MarkItDown
from openparse.schemas import Node, TextElement, Bbox, FileMetadata, NodeVariant

class DocumentParser:
    """Parser using Microsoft's MarkItDown for multiple file formats."""
    
    SUPPORTED_FORMATS = {'.pdf', '.docx', '.pptx', '.xlsx', '.html', '.txt', '.json', '.xml'}
    
    def __init__(self, use_ocr: bool = False, llm_client: Optional[object] = None):
        self.parser = MarkItDown(llm_client=llm_client) if llm_client else MarkItDown()
        self.use_ocr = use_ocr
        self.logger = logging.getLogger(__name__)

    def parse_batch(self, files: List[Path], batch_size: int = 1) -> List[Tuple[List[Node], FileMetadata]]:
        """Process multiple files in batches."""
        results = []
        for batch in range(0, len(files), batch_size):
            batch_files = files[batch:batch + batch_size]
            for file in batch_files:
                try:
                    result = self.parse(file)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"❌ Failed to parse {file}: {e}")
        return results
    

    def _get_metadata(self, result, file_path: Path) -> Dict:
        """Extract metadata from MarkItDown result."""
        stats = file_path.stat()
        return {
            "creation_date": None,
            "last_modified_date": date.fromtimestamp(stats.st_mtime),
            "last_accessed_date": date.fromtimestamp(stats.st_atime),
            "file_size": stats.st_size,
            "file_type": file_path.suffix.lower()
        }
    
    def parse(self, file: Union[str, Path]) -> tuple[List[Node], FileMetadata]:
        """Parse document into nodes using MarkItDown."""
        file_path = Path(file)
        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"❌ Unsupported file format: {file_path.suffix}")
            
        try:
            result = self.parser.convert(str(file_path))
            metadata = self._get_metadata(result, file_path)
            
            nodes = []
            for section in result.sections:
                if not section.text.strip():
                    continue
                    
                element = TextElement(
                    text=section.text,
                    lines=(),
                    bbox=Bbox(
                        page=section.page_number,
                        page_height=section.page_height or 1000,
                        page_width=section.page_width or 1000,
                        x0=section.x0 or 0,
                        y0=section.y0 or 0,
                        x1=section.x1 or 1000,
                        y1=section.y1 or 1000
                    ),
                    variant=NodeVariant.TEXT
                )
                nodes.append(Node(elements=(element,)))
            
            self.logger.debug(f"🔢 Created {len(nodes)} nodes from {len(result.sections)} sections.")
            return nodes, metadata
            
        except Exception as e:
            raise ValueError(f"❌ Failed to parse {file_path}: {str(e)}")
