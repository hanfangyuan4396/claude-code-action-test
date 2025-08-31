import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import OpenAI
from core.llm.openai_client import _create_openai_client, _iter_openai_tokens, openai_stream_iter


class TestCreateOpenAIClient:
    """测试 OpenAI 客户端创建功能"""

    def test_create_client_with_api_key_only(self, mocker):
        """测试仅使用 API Key 创建客户端"""
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", "test-api-key")
        mocker.patch("core.llm.openai_client.settings.OPENAI_BASE_URL", None)
        
        with patch("core.llm.openai_client.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            result = _create_openai_client()
            
            mock_openai.assert_called_once_with(api_key="test-api-key")
            assert result == mock_client

    def test_create_client_with_api_key_and_base_url(self, mocker):
        """测试使用 API Key 和 Base URL 创建客户端"""
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", "test-api-key")
        mocker.patch("core.llm.openai_client.settings.OPENAI_BASE_URL", "https://custom.openai.com")
        
        with patch("core.llm.openai_client.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            result = _create_openai_client()
            
            mock_openai.assert_called_once_with(
                api_key="test-api-key",
                base_url="https://custom.openai.com"
            )
            assert result == mock_client

    def test_create_client_missing_api_key(self, mocker):
        """测试缺少 API Key 时抛出异常"""
        mocker.patch("core.llm.openai_client.settings.OPENAI_API_KEY", None)
        
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not configured"):
            _create_openai_client()


class TestIterOpenAITokens:
    """测试 OpenAI 同步流式迭代功能"""

    def test_iter_openai_tokens_success(self, mocker):
        """测试成功迭代 OpenAI tokens"""
        # Mock 设置
        mock_client = Mock()
        mock_stream = Mock()
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=Mock(content="Hello"))]
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock(delta=Mock(content=" world"))]
        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock(delta=Mock(content="!"))]
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2, mock_chunk3]))
        
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        mocker.patch("core.llm.openai_client.settings.OPENAI_MODEL", "gpt-4")
        
        # 执行测试
        result = list(_iter_openai_tokens("Test prompt"))
        
        # 验证结果
        assert result == ["Hello", " world", "!"]
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            stream=True,
        )

    def test_iter_openai_tokens_default_model(self, mocker):
        """测试使用默认模型"""
        mock_client = Mock()
        mock_stream = Mock()
        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content="test"))]
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk]))
        
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        mocker.patch("core.llm.openai_client.settings.OPENAI_MODEL", None)
        
        result = list(_iter_openai_tokens("Test prompt"))
        
        assert result == ["test"]
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-5-mini",  # 默认模型
            messages=[{"role": "user", "content": "Test prompt"}],
            stream=True,
        )

    def test_iter_openai_tokens_skip_empty_choices(self, mocker):
        """测试跳过空的 choices"""
        mock_client = Mock()
        mock_stream = Mock()
        mock_chunk1 = Mock()
        mock_chunk1.choices = []
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock(delta=Mock(content="valid"))]
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2]))
        
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        mocker.patch("core.llm.openai_client.settings.OPENAI_MODEL", "gpt-4")
        
        result = list(_iter_openai_tokens("Test prompt"))
        
        assert result == ["valid"]

    def test_iter_openai_tokens_skip_empty_delta(self, mocker):
        """测试跳过空的 delta"""
        mock_client = Mock()
        mock_stream = Mock()
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=None)]
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock(delta=Mock(content="valid"))]
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2]))
        
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        mocker.patch("core.llm.openai_client.settings.OPENAI_MODEL", "gpt-4")
        
        result = list(_iter_openai_tokens("Test prompt"))
        
        assert result == ["valid"]

    def test_iter_openai_tokens_skip_empty_content(self, mocker):
        """测试跳过空的 content"""
        mock_client = Mock()
        mock_stream = Mock()
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=Mock(content=None))]
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock(delta=Mock(content="valid"))]
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2]))
        
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        mocker.patch("core.llm.openai_client.settings.OPENAI_MODEL", "gpt-4")
        
        result = list(_iter_openai_tokens("Test prompt"))
        
        assert result == ["valid"]

    def test_iter_openai_tokens_chunk_parsing_error(self, mocker):
        """测试分片解析错误的容错处理"""
        mock_client = Mock()
        mock_stream = Mock()
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=Mock(content="Hello"))]
        mock_chunk2 = Mock()
        # 模拟一个会引发异常的 chunk
        mock_chunk2.choices = [Mock()]
        mock_chunk2.choices[0].delta = Mock(side_effect=Exception("Parse error"))
        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock(delta=Mock(content=" world"))]
        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2, mock_chunk3]))
        
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        mocker.patch("core.llm.openai_client.settings.OPENAI_MODEL", "gpt-4")
        mock_logger = mocker.patch("core.llm.openai_client.logger")
        
        result = list(_iter_openai_tokens("Test prompt"))
        
        # 应该跳过错误的 chunk，继续处理后续的
        assert result == ["Hello", " world"]
        # 验证警告日志被记录
        mock_logger.warning.assert_called_once()


class TestOpenAIStreamIter:
    """测试 OpenAI 异步流式迭代功能"""

    @pytest.mark.asyncio
    async def test_openai_stream_iter_success(self, mocker):
        """测试异步流式迭代成功"""
        # Mock 同步迭代器
        mock_sync_iter = Mock(return_value=iter(["Hello", " ", "world"]))
        mocker.patch("core.llm.openai_client._iter_openai_tokens", mock_sync_iter)
        
        # 执行测试
        result = []
        async for token in openai_stream_iter("Test prompt"):
            result.append(token)
        
        assert result == ["Hello", " ", "world"]
        mock_sync_iter.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    async def test_openai_stream_iter_exception_propagation(self, mocker):
        """测试异常传播"""
        test_exception = Exception("Test error")
        mock_sync_iter = Mock(side_effect=test_exception)
        mocker.patch("core.llm.openai_client._iter_openai_tokens", mock_sync_iter)
        
        # 验证异常被正确传播
        with pytest.raises(Exception, match="Test error"):
            async for _ in openai_stream_iter("Test prompt"):
                pass