import pytest
from unittest.mock import patch, Mock
from loaders.document_loader import DocumentLoader

class TestDocumentLoader:
    def setup_method(self):
        self.loader = DocumentLoader()

    def test_load_pdf(self):
        with patch('loaders.document_loader.PyPDFLoader') as mock_pdf:
            mock_instance = Mock()
            mock_instance.load.return_value = [Mock(metadata={})]
            mock_pdf.return_value = mock_instance
            docs = self.loader.load_document('file.pdf', 'file.pdf')
            assert isinstance(docs, list)
            assert len(docs) == 1
            mock_pdf.assert_called_once()

    def test_load_txt(self):
        with patch('loaders.document_loader.TextLoader') as mock_txt:
            mock_instance = Mock()
            mock_instance.load.return_value = [Mock(metadata={})]
            mock_txt.return_value = mock_instance
            docs = self.loader.load_document('file.txt', 'file.txt')
            assert isinstance(docs, list)
            assert len(docs) == 1
            mock_txt.assert_called_once()

    def test_load_docx(self):
        with patch('loaders.document_loader.Docx2txtLoader') as mock_docx:
            mock_instance = Mock()
            mock_instance.load.return_value = [Mock(metadata={})]
            mock_docx.return_value = mock_instance
            docs = self.loader.load_document('file.docx', 'file.docx')
            assert isinstance(docs, list)
            assert len(docs) == 1
            mock_docx.assert_called_once()

    def test_load_unsupported_type(self):
        docs = self.loader.load_document('file.xyz', 'file.xyz')
        assert docs == []

    def test_split_documents(self):
        mock_doc = Mock()
        with patch.object(self.loader.text_splitter, 'split_documents', return_value=[mock_doc, mock_doc]) as mock_split:
            docs = self.loader.split_documents([mock_doc])
            assert isinstance(docs, list)
            assert len(docs) == 2
            mock_split.assert_called_once() 