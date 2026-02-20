"""Módulo para cargar documentos y preparar contenido para Context Caching de Gemini"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from ai.prompts import DOCUMENTS_CACHE_HEADER


class DocumentLoader:
    """Carga y prepara documentos para usar con Context Caching de Gemini"""
    
    def __init__(self, document_paths: List[str] = None, documents_dir: str = None):
        """
        Inicializa el cargador de documentos
        
        Args:
            document_paths: Lista de rutas a documentos específicos (opcional)
            documents_dir: Directorio que contiene múltiples documentos (opcional)
        """
        self.documents: Dict[str, str] = {}
        
        if document_paths:
            for doc_path in document_paths:
                self._load_document(doc_path)
        elif documents_dir:
            self._load_documents_from_dir(documents_dir)
        else:
            # Ruta por defecto
            default_path = Path(__file__).parent.parent.parent / "organizacion_xponencia_gabo.md"
            if os.path.exists(default_path):
                self._load_document(str(default_path))
    
    def _load_document(self, document_path: str):
        """Carga el contenido de un documento"""
        try:
            if os.path.exists(document_path):
                with open(document_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    doc_name = os.path.basename(document_path)
                    self.documents[doc_name] = content
                    print(f"Documento cargado: {doc_name}")
            else:
                print(f"Advertencia: Documento no encontrado: {document_path}")
        except Exception as e:
            print(f"Error cargando documento {document_path}: {e}")
    
    def _load_documents_from_dir(self, documents_dir: str):
        """Carga todos los documentos de un directorio"""
        try:
            dir_path = Path(documents_dir)
            if not dir_path.exists():
                print(f"Advertencia: Directorio no encontrado: {documents_dir}")
                return
            
            extensions = ['.md', '.txt', '.mdx']
            for ext in extensions:
                for file_path in dir_path.glob(f'*{ext}'):
                    self._load_document(str(file_path))
        except Exception as e:
            print(f"Error cargando documentos del directorio: {e}")
    
    def add_document(self, document_path: str):
        """Agrega un nuevo documento"""
        self._load_document(document_path)
    
    def remove_document(self, doc_name: str):
        """Elimina un documento por nombre"""
        if doc_name in self.documents:
            del self.documents[doc_name]
            print(f"Documento eliminado: {doc_name}")
    
    def get_content_for_cache(self) -> str:
        """
        Prepara todo el contenido de documentos para cachear en Gemini
        
        Returns:
            String con todo el contenido formateado para el cache
        """
        if not self.documents:
            return ""
        
        sections = []
        for doc_name, content in self.documents.items():
            sections.append(f"=== DOCUMENTO: {doc_name} ===\n\n{content}")
        
        return DOCUMENTS_CACHE_HEADER + "\n\n" + "="*50 + "\n\n".join(sections)
    
    def get_document_list(self) -> List[str]:
        """Retorna lista de nombres de documentos cargados"""
        return list(self.documents.keys())
    
    def get_document(self, doc_name: str) -> Optional[str]:
        """Retorna el contenido de un documento específico"""
        return self.documents.get(doc_name)
    
    def get_total_size(self) -> int:
        """Retorna el tamaño total en caracteres de todos los documentos"""
        return sum(len(content) for content in self.documents.values())
    
    def get_stats(self) -> dict:
        """Retorna estadísticas de los documentos cargados"""
        return {
            "total_documents": len(self.documents),
            "total_characters": self.get_total_size(),
            "documents": {
                name: len(content) for name, content in self.documents.items()
            }
        }


# Alias para compatibilidad con código existente
DocumentContext = DocumentLoader
