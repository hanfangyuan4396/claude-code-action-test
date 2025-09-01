import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import OpenAI

from core.llm.openai_client import _create_openai_client, _iter_openai_tokens, openai_stream_iter


class TestCreateOpenAIClient:
    """Test cases for _create_openai_client function."""

    def test_create_client_missing_api_key(self, mocker):
        """Test that missing API key raises RuntimeError."""
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", None)
        
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not configured"):
            _create_openai_client()

    def test_create_client_valid_api_key_only(self, mocker):
        """Test client creation with valid API key but no base URL."""
        mock_api_key = "test-api-key"
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", mock_api_key)
        mocker.patch("core.llm.openai_client.settings.OPENAI_BASE_URL", None)
        
        with patch("core.llm.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            result = _create_openai_client()
            
            mock_openai_class.assert_called_once_with(api_key=mock_api_key)
            assert result == mock_client

    def test_create_client_with_base_url(self, mocker):
        """Test client creation with both API key and base URL."""
        mock_api_key = "test-api-key"
        mock_base_url = "https://custom.openai.com/v1"
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", mock_api_key)
        mocker.patch("core.llm.openai_client.settings.OPENAI_BASE_URL", mock_base_url)
        
        with patch("core.llm.openai_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            result = _create_openai_client()
            
            mock_openai_class.assert_called_once_with(
                api_key=mock_api_key,
                base_url=mock_base_url
            )
            assert result == mock_client


class TestIterOpenAITokens:
    """Test cases for _iter_openai_tokens function."""

    def test_iter_tokens_successful_streaming(self, mocker):
        """Test successful token iteration from OpenAI stream."""
        mock_api_key = "test-key"
        mock_model = "gpt-4"
        mock_prompt = "Hello, world!"
        
        # Mock settings
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", mock_api_key)
        mocker.patch("core.llm.openai_client.settings.OPENAI_MODEL", mock_model)
        
        # Mock OpenAI client and stream
        mock_client = Mock()
        mock_stream = Mock()
        mock_client.chat.completions.create.return_value = mock_stream
        
        # Create mock chunks
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock()]
        mock_chunk1.choices[0].delta = Mock()
        mock_chunk1.choices[0].delta.content = "Hello"
        
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock()]
        mock_chunk2.choices[0].delta = Mock()
        mock_chunk2.choices[0].delta.content = ", world"
        
        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock()]
        mock_chunk3.choices[0].delta = Mock()
        mock_chunk3.choices[0].delta.content = "!"
        
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2, mock_chunk3]))
        
        with patch("core.llm.openai_client._create_openai_client", return_value=mock_client):
            result = list(_iter_openai_tokens(mock_prompt))
            
            assert result == ["Hello", ", world", "!"]
            mock_client.chat.completions.create.assert_called_once_with(
                model=mock_model,
                messages=[{"role": "user", "content": mock_prompt}],
                stream=True,
            )

    def test_iter_tokens_skip_empty_choices(self, mocker):
        """Test that chunks without choices are skipped."""
        mock_api_key = "test-key"
        mock_prompt = "test"
        
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", mock_api_key)
        
        mock_client = Mock()
        mock_stream = Mock()
        
        # Create chunk with no choices
        mock_chunk = Mock()
        mock_chunk.choices = []
        
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
        
        with patch("core.llm.openai_client._create_openai_client", return_value=mock_client):
            result = list(_iter_openai_tokens(mock_prompt))
            
            assert result == []

    def test_iter_tokens_skip_empty_delta(self, mocker):
        """Test that chunks with choices but no delta are skipped."""
        mock_api_key = "test-key"
        mock_prompt = "test"
        
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", mock_api_key)
        
        mock_client = Mock()
        mock_stream = Mock()
        
        # Create chunk with choice but no delta
        mock_chunk = Mock()
        mock_chunk.choices = [Mock()]
        mock_chunk.choices[0].delta = None
        
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
        
        with patch("core.llm.openai_client._create_openai_client", return_value=mock_client):
            result = list(_iter_openai_tokens(mock_prompt))
            
            assert result == []

    def test_iter_tokens_skip_empty_content(self, mocker):
        """Test that chunks with delta but no content are skipped."""
        mock_api_key = "test-key"
        mock_prompt = "test"
        
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", mock_api_key)
        
        mock_client = Mock()
        mock_stream = Mock()
        
        # Create chunk with delta but no content
        mock_chunk = Mock()
        mock_chunk.choices = [Mock()]
        mock_chunk.choices[0].delta = Mock()
        mock_chunk.choices[0].delta.content = None
        
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
        
        with patch("core.llm.openai_client._create_openai_client", return_value=mock_client):
            result = list(_iter_openai_tokens(mock_prompt))
            
            assert result == []

    def test_iter_tokens_chunk_parsing_error_handling(self, mocker):
        """Test that chunk parsing errors are logged and don't break the stream."""
        mock_api_key = "test-key"
        mock_prompt = "test"
        
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", mock_api_key)
        
        mock_client = Mock()
        mock_stream = Mock()
        
        # Create chunk that will raise an exception during parsing
        mock_chunk = Mock()
        mock_chunk.choices = [Mock()]
        mock_chunk.choices[0].delta = Mock()
        # Simulate an error when accessing content
        del mock_chunk.choices[0].delta.content
        
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
        
        with patch("core.llm.openai_client._create_openai_client", return_value=mock_client), \
             patch("core.llm.openai_client.logger") as mock_logger:
            
            result = list(_iter_openai_tokens(mock_prompt))
            
            assert result == []
            mock_logger.warning.assert_called_once()

    def test_iter_tokens_default_model(self, mocker):
        """Test that default model is used when OPENAI_MODEL is not set."""
        mock_api_key = "test-key"
        mock_prompt = "test"
        
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", mock_api_key)
        mocker.patch("core.llm.openai_client.settings.OPENAI_MODEL", None)
        
        mock_client = Mock()
        mock_stream = Mock()
        mock_stream.__iter__ = Mock(return_value=iter([]))
        
        with patch("core.llm.openai_client._create_openai_client", return_value=mock_client):
            list(_iter_openai_tokens(mock_prompt))
            
            # Verify default model is used
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-5-mini"


class TestOpenAIStreamIter:
    """Test cases for openai_stream_iter async function."""

    @pytest.mark.asyncio
    async def test_openai_stream_iter_successful(self, mocker):
        """Test successful async streaming iteration."""
        mock_prompt = "Hello"
        
        # Mock the sync iterator to return some tokens
        mock_tokens = ["Hello", ", ", "world", "!"]
        
        with patch("core.llm.openai_client._iter_openai_tokens", return_value=iter(mock_tokens)), \
             patch("core.llm.openai_client.threading.Thread") as mock_thread_class, \
             patch("core.llm.openai_client.asyncio.to_thread") as mock_to_thread:
            
            # Mock queue behavior
            async def mock_to_thread_impl(func):
                # Simulate queue.get() behavior
                queue_items = mock_tokens + [None]  # None is sentinel
                for item in queue_items:
                    yield item
            
            # Setup mock thread
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread
            
            # Mock asyncio.to_thread to return queue items
            side_effects = mock_tokens + [None]  # None is sentinel
            mock_to_thread.side_effect = side_effects
            
            # Collect results
            result = []
            async for token in openai_stream_iter(mock_prompt):
                result.append(token)
            
            assert result == mock_tokens
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_stream_iter_exception_handling(self, mocker):
        """Test that exceptions from the producer thread are properly raised."""
        mock_prompt = "Hello"
        test_exception = RuntimeError("Test error")
        
        with patch("core.llm.openai_client._iter_openai_tokens") as mock_iter, \
             patch("core.llm.openai_client.threading.Thread") as mock_thread_class, \
             patch("core.llm.openai_client.asyncio.to_thread") as mock_to_thread:
            
            # Mock the sync iterator to raise an exception
            mock_iter.side_effect = test_exception
            
            # Mock asyncio.to_thread to return the exception then sentinel
            mock_to_thread.side_effect = [test_exception, None]
            
            # Should raise the exception
            with pytest.raises(RuntimeError, match="Test error"):
                async for _ in openai_stream_iter(mock_prompt):
                    pass

    @pytest.mark.asyncio
    async def test_openai_stream_iter_thread_creation(self, mocker):
        """Test that producer thread is created with correct parameters."""
        mock_prompt = "test"
        
        with patch("core.llm.openai_client._iter_openai_tokens", return_value=iter([])), \
             patch("core.llm.openai_client.threading.Thread") as mock_thread_class, \
             patch("core.llm.openai_client.asyncio.to_thread", return_value=None):
            
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread
            
            # Consume the async generator
            async for _ in openai_stream_iter(mock_prompt):
                pass
            
            # Verify thread creation
            mock_thread_class.assert_called_once()
            call_args = mock_thread_class.call_args
            assert call_args[1]["daemon"] is True
            
            # Verify thread was started
            mock_thread.start.assert_called_once()