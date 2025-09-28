import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.core.ai_utils import AIUtils, GeminiService, AIService


class TestAIService:
    """Tests for the AIService abstract base class"""

    def test_abstract_methods(self):
        """Test that AIService defines the expected abstract methods"""
        # This is more of a documentation test - we can't instantiate abstract class
        expected_methods = ["generate_text", "analyze_code", "stream_text"]
        actual_methods = [
            method for method in dir(AIService) if not method.startswith("_")
        ]
        for method in expected_methods:
            assert method in actual_methods


class TestGeminiService:
    """Tests for the GeminiService class"""

    def test_init_with_api_key(self):
        """Test GeminiService initialization with API key"""
        with patch("src.core.ai_utils.genai.Client") as mock_client:
            service = GeminiService(api_key="test_key")
            assert service.api_key == "test_key"
            assert service._client is not None
            mock_client.assert_called_once_with(api_key="test_key")

    def test_init_without_api_key(self):
        """Test GeminiService initialization without API key"""
        with patch.dict("os.environ", {}, clear=True):
            with patch("src.core.ai_utils.get_logger") as mock_logger:
                service = GeminiService()
                assert service.api_key is None
                assert service._client is None
                mock_logger.return_value.warning.assert_called_once()

    def test_init_with_env_api_key(self):
        """Test GeminiService initialization with API key from environment"""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "env_key"}):
            with patch("src.core.ai_utils.genai.Client") as mock_client:
                service = GeminiService()
                assert service.api_key == "env_key"
                mock_client.assert_called_once_with(api_key="env_key")

    def test_init_client_failure(self):
        """Test GeminiService handles client initialization failure"""
        with patch(
            "src.core.ai_utils.genai.Client", side_effect=Exception("Init failed")
        ):
            with patch("src.core.ai_utils.get_logger") as mock_logger:
                service = GeminiService(api_key="test_key")
                assert service._client is None
                mock_logger.return_value.error.assert_called_once()

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_generate_text_success(self, mock_logger):
        """Test successful text generation"""
        mock_response = MagicMock()
        mock_response.text = "Generated text"

        with patch("src.core.ai_utils.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key")
            result = await service.generate_text("Test prompt")

            assert result == "Generated text"
            mock_client.models.generate_content.assert_called_once()

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_generate_text_no_client(self, mock_logger):
        """Test text generation without initialized client"""
        with patch.dict("os.environ", {}, clear=True):  # Ensure no API key
            service = GeminiService()  # No API key
            with pytest.raises(ValueError, match="Gemini client not initialized"):
                await service.generate_text("Test prompt")

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, mock_logger):
        """Test text generation with API error"""
        from google.genai.errors import APIError

        with patch("src.core.ai_utils.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = APIError(
                code=400, response_json={}, response="API Error"
            )
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key")
            with pytest.raises(APIError):
                await service.generate_text("Test prompt")

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_generate_text_timeout(self, mock_logger):
        """Test text generation timeout"""
        with patch("src.core.ai_utils.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            # Simulate a long-running operation that times out
            mock_client.models.generate_content = MagicMock()
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key")

            # Mock asyncio.wait_for to raise TimeoutError
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                with pytest.raises(TimeoutError, match="Text generation timed out"):
                    await service.generate_text("Test prompt")

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_generate_text_empty_response(self, mock_logger):
        """Test text generation with empty response"""
        mock_response = MagicMock()
        mock_response.text = None

        with patch("src.core.ai_utils.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key")
            result = await service.generate_text("Test prompt")

            assert result == ""

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_analyze_code(self, mock_logger):
        """Test code analysis"""
        mock_response = MagicMock()
        mock_response.text = "Code analysis result"

        with patch("src.core.ai_utils.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key")
            result = await service.analyze_code("def test(): pass")

            assert result == {"analysis": "Code analysis result"}

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_stream_text_success(self, mock_logger):
        """Test successful streaming text generation"""
        mock_chunks = [
            MagicMock(text="Hello "),
            MagicMock(text="world"),
            MagicMock(text="!"),
        ]

        with patch("src.core.ai_utils.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_stream = MagicMock()
            mock_stream.__iter__.return_value = mock_chunks
            mock_client.models.generate_content_stream.return_value = mock_stream
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key")
            chunks = []
            async for chunk in service.stream_text("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello ", "world", "!"]

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_stream_text_no_client(self, mock_logger):
        """Test streaming without initialized client"""
        with patch.dict("os.environ", {}, clear=True):  # Ensure no API key
            service = GeminiService()  # No API key
            chunks = []
            async for chunk in service.stream_text("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Error: Gemini client not initialized"]

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_stream_text_api_error(self, mock_logger):
        """Test streaming with API error"""
        from google.genai.errors import APIError

        with patch("src.core.ai_utils.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content_stream.side_effect = APIError(
                code=400, response_json={}, response=None
            )
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key")
            chunks = []
            async for chunk in service.stream_text("Test prompt"):
                chunks.append(chunk)

            assert len(chunks) == 1
            assert chunks[0].startswith("Error:")


class TestAIUtils:
    """Tests for the AIUtils class"""

    def test_init(self):
        """Test AIUtils initialization"""
        with patch("src.core.ai_utils.GeminiService") as mock_gemini:
            utils = AIUtils()
            assert "gemini" in utils.services
            mock_gemini.assert_called_once()

    def test_get_service_existing(self):
        """Test getting an existing service"""
        with patch("src.core.ai_utils.GeminiService"):
            utils = AIUtils()
            service = utils.get_service("gemini")
            assert service is not None

    def test_get_service_nonexistent(self):
        """Test getting a nonexistent service"""
        with patch("src.core.ai_utils.GeminiService"):
            utils = AIUtils()
            service = utils.get_service("nonexistent")
            assert service is None

    def test_add_service(self):
        """Test adding a custom service"""
        with patch("src.core.ai_utils.GeminiService"):
            utils = AIUtils()
            custom_service = MagicMock(spec=AIService)
            utils.add_service("custom", custom_service)

            assert "custom" in utils.services
            assert utils.services["custom"] == custom_service

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_generate_text_success(self, mock_logger):
        """Test successful text generation through AIUtils"""
        with patch("src.core.ai_utils.GeminiService") as mock_gemini_class:
            mock_service = MagicMock()
            mock_service.generate_text = AsyncMock(return_value="Generated text")
            mock_gemini_class.return_value = mock_service

            utils = AIUtils()
            result = await utils.generate_text("Test prompt")

            assert result == "Generated text"
            mock_service.generate_text.assert_called_once_with("Test prompt")

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_generate_text_service_not_found(self, mock_logger):
        """Test text generation with nonexistent service"""
        with patch("src.core.ai_utils.GeminiService"):
            utils = AIUtils()
            with pytest.raises(ValueError, match="AI service 'nonexistent' not found"):
                await utils.generate_text("Test prompt", service="nonexistent")

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_analyze_code_success(self, mock_logger):
        """Test successful code analysis through AIUtils"""
        with patch("src.core.ai_utils.GeminiService") as mock_gemini_class:
            mock_service = MagicMock()
            mock_service.analyze_code = AsyncMock(return_value={"analysis": "result"})
            mock_gemini_class.return_value = mock_service

            utils = AIUtils()
            result = await utils.analyze_code("def test(): pass")

            assert result == {"analysis": "result"}
            mock_service.analyze_code.assert_called_once_with("def test(): pass")

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_analyze_code_service_not_found(self, mock_logger):
        """Test code analysis with nonexistent service"""
        with patch("src.core.ai_utils.GeminiService"):
            utils = AIUtils()
            with pytest.raises(ValueError, match="AI service 'nonexistent' not found"):
                await utils.analyze_code("def test(): pass", service="nonexistent")

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_stream_text_success(self, mock_logger):
        """Test successful streaming text through AIUtils"""

        async def mock_generator():
            yield "Hello "
            yield "world"

        with patch("src.core.ai_utils.GeminiService") as mock_gemini_class:
            mock_service = MagicMock()
            mock_service.stream_text = AsyncMock(return_value=mock_generator())
            mock_gemini_class.return_value = mock_service

            utils = AIUtils()
            chunks = []
            async for chunk in utils.stream_text("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello ", "world"]

    @patch("src.core.ai_utils.get_logger")
    @pytest.mark.asyncio
    async def test_stream_text_service_not_found(self, mock_logger):
        """Test streaming text with nonexistent service"""
        with patch("src.core.ai_utils.GeminiService"):
            utils = AIUtils()
            with pytest.raises(ValueError, match="AI service 'nonexistent' not found"):
                async for chunk in utils.stream_text(
                    "Test prompt", service="nonexistent"
                ):
                    pass
