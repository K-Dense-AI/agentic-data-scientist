"""
Web operation tools for ADK agents.

Provides HTTP GET functionality with timeout and user-agent configuration.
"""

from typing import Optional

import requests


def fetch_url(
    url: str,
    timeout: int = 30,
    user_agent: Optional[str] = None,
) -> str:
    """
    Fetch content from a URL using HTTP GET.

    Parameters
    ----------
    url : str
        The URL to fetch
    timeout : int, optional
        Request timeout in seconds, default 30
    user_agent : str, optional
        Custom User-Agent header, default None (uses requests default)

    Returns
    -------
    str
        Response content or error message

    Notes
    -----
    - Only HTTP and HTTPS protocols are supported
    - Follows redirects automatically
    - Returns text content with automatic encoding detection
    - Returns error message for failed requests

    Examples
    --------
    >>> content = fetch_url("https://example.com")
    >>> print(content[:100])  # First 100 characters

    >>> content = fetch_url(
    ...     "https://api.example.com/data",
    ...     timeout=10,
    ...     user_agent="MyBot/1.0"
    ... )
    """
    try:
        # Validate URL scheme
        if not url.startswith(("http://", "https://")):
            return "Error: Only HTTP and HTTPS URLs are supported"
        
        # Set up headers
        headers = {}
        if user_agent is not None:
            headers["User-Agent"] = user_agent
        
        # Make the request
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        return response.text
    
    except requests.exceptions.Timeout:
        return f"Error: Request timed out after {timeout} seconds"
    except requests.exceptions.ConnectionError:
        return f"Error: Failed to connect to {url}"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.reason}"
    except requests.exceptions.RequestException as e:
        return f"Error: Request failed - {e}"
    except Exception as e:
        return f"Error fetching URL: {e}"

