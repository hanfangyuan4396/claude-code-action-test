from typing import Dict, Any


class EchoService:
    def build_echo_get_response(self, headers: Dict[str, Any], query_params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "method": "GET",
            "headers": headers,
            "query": query_params,
        }
