import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from core.llm.openai_client import _create_openai_client, openai_stream_iter


class TestOpenAIIntegration:
    """OpenAI 集成测试"""

    @pytest.fixture
    def mock_openai_settings(self, monkeypatch):
        """设置测试用的 OpenAI 配置"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("LLM_PROVIDER", "openai")

    def test_create_real_client(self, mock_openai_settings):
        """测试创建真实的 OpenAI 客户端"""
        client = _create_openai_client()
        
        assert isinstance(client, Mock) is False  # 真实客户端不是 Mock
        assert client.api_key == "test-api-key"
        assert client.base_url == "https://api.openai.com/v1"

    @pytest.mark.asyncio
    async def test_stream_integration_mocked(self, mock_openai_settings, mocker):
        """测试流式集成（使用 Mock 响应）"""
        # Mock OpenAI 客户端
        mock_client = Mock()
        mock_stream = Mock()
        
        # 模拟流式响应
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=Mock(content="Hello"))]
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock(delta=Mock(content=" "))]
        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock(delta=Mock(content="world"))]
        mock_chunk4 = Mock()
        mock_chunk4.choices = [Mock(delta=Mock(content=None))]  # 结束标记
        
        mock_stream.__aiter__ = AsyncMock(return_value=asyncio.AsyncIterator([mock_chunk1, mock_chunk2, mock_chunk3, mock_chunk4]))
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        
        # 执行测试
        result = []
        async for token in openai_stream_iter("Test prompt"):
            result.append(token)
        
        assert result == ["Hello", " ", "world"]
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            stream=True,
        )

    def test_client_configuration_validation(self, monkeypatch):
        """测试客户端配置验证"""
        # 测试缺少 API Key
        monkeypatch.setenv("OPENAI_API_KEY", "")
        
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not configured"):
            _create_openai_client()

    def test_client_with_custom_base_url(self, monkeypatch):
        """测试自定义 Base URL"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://custom-proxy.com/v1")
        
        with patch("core.llm.openai_client.OpenAI") as mock_openai:
            _create_openai_client()
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://custom-proxy.com/v1"
            )

    def test_client_without_custom_base_url(self, monkeypatch):
        """测试不使用自定义 Base URL"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "")
        
        with patch("core.llm.openai_client.OpenAI") as mock_openai:
            _create_openai_client()
            mock_openai.assert_called_once_with(api_key="test-key")

    @pytest.mark.asyncio
    async def test_stream_error_handling(self, mock_openai_settings, mocker):
        """测试流式错误处理"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        
        # 验证异常被正确传播
        with pytest.raises(Exception, match="API Error"):
            async for _ in openai_stream_iter("Test prompt"):
                pass

    @pytest.mark.asyncio
    async def test_stream_empty_response(self, mock_openai_settings, mocker):
        """测试空流式响应"""
        mock_client = Mock()
        mock_stream = Mock()
        mock_stream.__aiter__ = AsyncMock(return_value=asyncio.AsyncIterator([]))
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        
        # 执行测试
        result = []
        async for token in openai_stream_iter("Test prompt"):
            result.append(token)
        
        assert result == []

    @pytest.mark.asyncio 
    async def test_stream_mixed_valid_invalid_chunks(self, mock_openai_settings, mocker):
        """测试混合有效和无效的分片"""
        mock_client = Mock()
        mock_stream = Mock()
        
        # 创建混合的有效和无效分片
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=Mock(content="Hello"))]
        mock_chunk2 = Mock()
        mock_chunk2.choices = []  # 无效分片
        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock(delta=None)]  # 无效分片
        mock_chunk4 = Mock()
        mock_chunk4.choices = [Mock(delta=Mock(content=" world"))]
        
        mock_stream.__aiter__ = AsyncMock(return_value=asyncio.AsyncIterator([mock_chunk1, mock_chunk2, mock_chunk3, mock_chunk4]))
        mock_client.chat.completions.create.return_value = mock_stream
        
        mocker.patch("core.llm.openai_client._create_openai_client", return_value=mock_client)
        mock_logger = mocker.patch("core.llm.openai_client.logger")
        
        # 执行测试
        result = []
        async for token in openai_stream_iter("Test prompt"):
            result.append(token)
        
        # 应该只包含有效的 tokens
        assert result == ["Hello", " world"]


class AsyncIterator:
    """辅助类：创建异步迭代器"""
    def __init__(self, items):
        self.items = items
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item