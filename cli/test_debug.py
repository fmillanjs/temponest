from click.testing import CliRunner
from unittest.mock import patch, Mock
from temponest_cli.cli import cli

def test_debug():
    runner = CliRunner()
    mock_agent = Mock(
        id="agent-123",
        name="Test Agent",
        model="llama3.2:latest",
        provider="ollama",
        temperature=0.7,
        tools=["search"],
    )
    mock_client = Mock()
    mock_client.agents.list.return_value = [mock_agent]
    
    with patch("temponest_cli.cli.get_client", return_value=mock_client):
        result = runner.invoke(cli, ["agent", "list"])
    
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    if result.exception:
        print(f"Exception: {result.exception}")
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

if __name__ == "__main__":
    test_debug()
